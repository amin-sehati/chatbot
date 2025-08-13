import json
import os
import traceback
import sys
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from tavily import TavilyClient


# Add detailed logging function
def log_debug(message, level="INFO"):
    """Log debug information that will appear in Vercel logs"""
    print(f"[{level}] {message}", file=sys.stderr)
    sys.stderr.flush()


# Pydantic models for database schema
class CompanyMaster(BaseModel):
    id: Optional[str] = None
    name: str
    websiteUrl: Optional[str] = None
    wikipediaUrl: Optional[str] = None
    linkedinUrl: Optional[str] = None
    logoUrl: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    tagsMaster: List[str] = Field(default_factory=list)
    naicsCode: Optional[str] = None
    stillInBusiness: Optional[bool] = None


class Company(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    personalNote: Optional[str] = None
    companyMasterId: Optional[str] = None


# API request/response models
class CompanySearchRequest(BaseModel):
    name: str
    personalNote: str
    tags: str


class SimilarCompanyResult(BaseModel):
    company: CompanyMaster
    justification: str


class CompanySearchResponse(BaseModel):
    inputCompany: CompanySearchRequest
    similarCompanies: List[SimilarCompanyResult]


# Create FastAPI app
app = FastAPI(title="Company Search API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY")

log_debug(f"GROQ_API_KEY present: {'Yes' if GROQ_API_KEY else 'No'}")
log_debug(f"TAVILY_API_KEY present: {'Yes' if TAVILY_API_KEY else 'No'}")


# Health check endpoint
@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "service": "Company Search API",
        "groq_key_present": bool(GROQ_API_KEY),
        "tavily_key_present": bool(TAVILY_API_KEY),
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


def search_similar_companies(name: str, personal_note: str, tags: str) -> List[dict]:
    """Search for similar companies using Tavily with enhanced detail search"""
    if not TAVILY_API_KEY:
        log_debug("Tavily API key not configured", "ERROR")
        return []

    try:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

        # Step 1: Initial broad search to identify similar companies
        search_query = f"companies similar to {name} in {personal_note} industry with focus on {tags}"
        log_debug(f"Initial search query: {search_query}")

        initial_response = tavily_client.search(search_query, search_depth="advanced")

        # Step 2: Extract potential company names from initial results
        initial_results = []
        company_names = set()

        for result in initial_response.get("results", [])[:8]:  # Get top 8 results
            initial_results.append(
                {
                    "title": result.get("title", ""),
                    "content": result.get("content", ""),
                    "url": result.get("url", ""),
                    "published_date": result.get("published_date", ""),
                }
            )

            # Extract potential company names from titles and content
            content = f"{result.get('title', '')} {result.get('content', '')}"
            # Simple extraction - look for capitalized words that might be company names
            words = content.split()
            for i, word in enumerate(words):
                if word.istitle() and len(word) > 3 and i < len(words) - 1:
                    if words[i + 1].istitle() or word.endswith(
                        ("Inc", "Corp", "Ltd", "LLC")
                    ):
                        company_names.add(word)

        # Step 3: Do targeted searches for top company candidates
        all_results = initial_results.copy()

        # Limit to top 5 potential companies to avoid too many API calls
        for company_name in list(company_names)[:5]:
            if (
                company_name.lower() != name.lower()
            ):  # Don't search for the input company
                try:
                    detailed_query = f"{company_name} company website linkedin wikipedia description industry business bankruptcy liquidation closure ceased"
                    log_debug(f"Detailed search for: {company_name}")

                    detailed_response = tavily_client.search(
                        detailed_query, search_depth="basic"
                    )

                    for result in detailed_response.get("results", [])[
                        :3
                    ]:  # Top 3 results per company
                        all_results.append(
                            {
                                "title": result.get("title", ""),
                                "content": result.get("content", ""),
                                "url": result.get("url", ""),
                                "published_date": result.get("published_date", ""),
                                "target_company": company_name,  # Mark which company this search was for
                            }
                        )
                except Exception as e:
                    log_debug(
                        f"Error in detailed search for {company_name}: {e}", "ERROR"
                    )
                    continue

        log_debug(f"Found {len(all_results)} total search results (initial + detailed)")
        return all_results

    except Exception as e:
        log_debug(f"Tavily search error: {e}", "ERROR")
        return []


def process_with_llm(
    search_results: List[dict], input_company: CompanySearchRequest
) -> List[SimilarCompanyResult]:
    """Process search results with LLM to extract structured company data"""
    if not GROQ_API_KEY:
        log_debug("GROQ API key not configured", "ERROR")
        return []

    try:
        model = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=GROQ_API_KEY,
            temperature=0,
        )

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert business analyst. Given comprehensive search results about companies (including both general similarity searches and detailed company-specific searches), extract information for exactly 5 similar companies to the input company.

CRITICAL: Use the search results to fill out ALL available fields. The search results include both general similarity data and detailed company-specific information.

STRICT MATCHING REQUIREMENT: Only select companies that match ALL of the specified criteria:
- Must relate to ALL tags provided (not just some)
- Must align with the business focus described in the personal note
- Must be genuinely similar to the input company

Input company details:
Name: {input_name}
Personal Note: {input_note}
Tags: {input_tags}

IMPORTANT: Reject companies that don't match all the specified tags and business focus. The search was designed to find companies that satisfy ALL criteria as AND conditions.

For each company, extract and fill these fields using the search data:
- name: Full official company name (required)
- websiteUrl: Official company website URL (look for company homepage, corporate site)
- wikipediaUrl: Wikipedia page URL (look for "wikipedia.org/wiki/CompanyName")
- linkedinUrl: LinkedIn company page URL (look for "linkedin.com/company/")
- logoUrl: Company logo image URL if available
- description: Comprehensive 2-3 sentence company description including business focus, market position, and key products/services
- industry: Specific primary industry/sector (be precise: "Electric Vehicles", "Cloud Computing", etc.)
- tagsMaster: 4-6 relevant tags based on business activities, technologies, market focus
- naicsCode: NAICS industry classification code if mentioned
- stillInBusiness: Boolean indicating current business status. Set to FALSE if search results mention: bankruptcy, liquidation, ceased operations, out of business, closed down, shut down, dissolved, acquired and discontinued. Set to TRUE only if actively operating. Set to null if completely uncertain.

Return JSON array with exactly 5 companies:
{{
  "company": {{
    "name": "Full Official Company Name",
    "websiteUrl": "https://company-website.com",
    "wikipediaUrl": "https://en.wikipedia.org/wiki/Company_Name", 
    "linkedinUrl": "https://www.linkedin.com/company/company-name/",
    "logoUrl": "https://logo-url.com/logo.png",
    "description": "Detailed description of company's business, products, and market position.",
    "industry": "Specific Industry Name",
    "tagsMaster": ["tag1", "tag2", "tag3", "tag4"],
    "naicsCode": "123456",
    "stillInBusiness": null
  }},
  "justification": "First explain how this company matches ALL required criteria: [specify how it relates to each tag from '{input_tags}' and aligns with '{input_note}']. Then detail similarities to {input_name} (business model, technology, market parallels), followed by key differences (market focus, business model variations, geographic scope, etc.). Be comprehensive and balanced."
}}

IMPORTANT: 
- Use actual URLs found in search results, not placeholders
- If a field cannot be determined from search results, set it to null
- Prioritize companies with the most complete information available
- Make descriptions detailed and informative
- Include both similarities AND differences in justifications for balanced analysis
- FOR BUSINESS STATUS: Be conservative - only set stillInBusiness=true if clearly active. Look specifically for recent news, bankruptcy filings, closure announcements. When in doubt, use null.""",
                ),
                ("human", "Search results:\n{search_results}"),
            ]
        )

        # Prepare search results text with better organization
        results_text = "=== SIMILARITY SEARCH RESULTS ===\n"
        general_results = [r for r in search_results if "target_company" not in r]
        targeted_results = [r for r in search_results if "target_company" in r]

        # Add general similarity results
        for i, result in enumerate(general_results, 1):
            results_text += f"\n{i}. GENERAL: {result['title']}\n"
            results_text += f"Content: {result['content']}\n"
            results_text += f"URL: {result['url']}\n"
            results_text += "-" * 50 + "\n"

        # Add company-specific detailed results
        if targeted_results:
            results_text += "\n=== DETAILED COMPANY INFORMATION ===\n"
            current_company = ""
            for result in targeted_results:
                target_company = result.get("target_company", "")
                if target_company != current_company:
                    current_company = target_company
                    results_text += f"\n--- DETAILS FOR: {target_company} ---\n"

                results_text += f"Title: {result['title']}\n"
                results_text += f"Content: {result['content']}\n"
                results_text += f"URL: {result['url']}\n"
                results_text += "-" * 30 + "\n"

        # Generate response
        chain = prompt | model
        response = chain.invoke(
            {
                "input_name": input_company.name,
                "input_note": input_company.personalNote,
                "input_tags": input_company.tags,
                "search_results": results_text,
            }
        )

        log_debug(f"LLM response length: {len(response.content)}")

        # Parse JSON response
        try:
            # Extract JSON from markdown code blocks if present
            content = response.content.strip()

            # Look for JSON in code blocks
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()
            elif "```" in content:
                # Handle plain code blocks
                start = content.find("```") + 3
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()

            # Try to find JSON array start if there's still extra text
            if not content.startswith("["):
                bracket_start = content.find("[")
                if bracket_start != -1:
                    content = content[bracket_start:]

            parsed_response = json.loads(content)

            # Validate and convert to SimilarCompanyResult objects
            similar_companies = []
            for i, item in enumerate(parsed_response[:5]):  # Ensure max 5 companies
                company_data = item.get("company", {})
                justification = item.get("justification", "").strip()

                # Debug logging
                log_debug(
                    f"Processing company {i+1}: {company_data.get('name', 'Unknown')}"
                )
                log_debug(f"Justification length: {len(justification)}")

                # Ensure we have a justification
                if not justification:
                    justification = f"Similar to {input_company.name} based on industry and business focus."

                company = CompanyMaster(
                    name=company_data.get("name", ""),
                    websiteUrl=company_data.get("websiteUrl"),
                    wikipediaUrl=company_data.get("wikipediaUrl"),
                    linkedinUrl=company_data.get("linkedinUrl"),
                    logoUrl=company_data.get("logoUrl"),
                    description=company_data.get("description", ""),
                    industry=company_data.get("industry", ""),
                    tagsMaster=company_data.get("tagsMaster", []),
                    naicsCode=company_data.get("naicsCode"),
                    stillInBusiness=company_data.get("stillInBusiness"),
                )

                similar_companies.append(
                    SimilarCompanyResult(company=company, justification=justification)
                )

            log_debug(f"Successfully processed {len(similar_companies)} companies")
            return similar_companies

        except json.JSONDecodeError as e:
            log_debug(f"JSON parsing error: {e}", "ERROR")
            log_debug(f"Raw response: {response.content}", "ERROR")
            return []

    except Exception as e:
        log_debug(f"LLM processing error: {e}", "ERROR")
        log_debug(f"Traceback: {traceback.format_exc()}", "ERROR")
        return []


@app.post("/search-companies", response_model=CompanySearchResponse)
async def search_companies_endpoint(request: CompanySearchRequest):
    """Search for similar companies based on input company details"""
    log_debug(f"Received company search request: {request.name}")

    try:
        # Step 1: Search with Tavily
        search_results = search_similar_companies(
            request.name, request.personalNote, request.tags
        )

        if not search_results:
            raise HTTPException(
                status_code=500, detail="Failed to retrieve search results"
            )

        # Step 2: Process with LLM
        similar_companies = process_with_llm(search_results, request)

        if not similar_companies:
            raise HTTPException(
                status_code=500, detail="Failed to process search results with LLM"
            )

        # Step 3: Return structured response
        response = CompanySearchResponse(
            inputCompany=request, similarCompanies=similar_companies
        )

        log_debug(
            f"Successfully processed search for {request.name}, found {len(similar_companies)} similar companies"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        log_debug(f"Company search error: {e}", "ERROR")
        log_debug(f"Traceback: {traceback.format_exc()}", "ERROR")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "groq_key_present": bool(GROQ_API_KEY),
                "tavily_key_present": bool(TAVILY_API_KEY),
            },
        )


# Legacy endpoints for compatibility (if needed)
@app.post("/chat")
@app.post("/api/chat")
async def legacy_chat():
    """Legacy chat endpoint - returns redirect message"""
    return JSONResponse(
        content={"message": "This endpoint has been replaced with /search-companies"},
        status_code=200,
    )


# Vercel-compatible handler
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            log_debug(f"=== REQUEST START === Path: {self.path}")
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            log_debug(f"Request body parsed successfully")

            if self.path == "/api/search-companies":
                log_debug("Routing to search companies handler")

                # Process the request
                request = CompanySearchRequest(**data)

                # Search with Tavily
                search_results = search_similar_companies(
                    request.name, request.personalNote, request.tags
                )

                if not search_results:
                    response = {
                        "status": 500,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps(
                            {"error": "Failed to retrieve search results"}
                        ),
                    }
                else:
                    # Process with LLM
                    similar_companies = process_with_llm(search_results, request)

                    if not similar_companies:
                        response = {
                            "status": 500,
                            "headers": {"Content-Type": "application/json"},
                            "body": json.dumps(
                                {"error": "Failed to process search results with LLM"}
                            ),
                        }
                    else:
                        # Create response
                        result = CompanySearchResponse(
                            inputCompany=request, similarCompanies=similar_companies
                        )

                        response = {
                            "status": 200,
                            "headers": {"Content-Type": "application/json"},
                            "body": result.model_dump_json(),
                        }
            else:
                log_debug(f"Unknown path: {self.path}")
                response = {
                    "status": 404,
                    "headers": {"Content-Type": "text/plain"},
                    "body": "Not Found",
                }

            # Send response
            log_debug(f"Sending response with status {response['status']}")
            self.send_response(response["status"])
            for key, value in response["headers"].items():
                self.send_header(key, value)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(response["body"].encode("utf-8"))
            log_debug("=== REQUEST COMPLETE ===")

        except Exception as e:
            error_details = traceback.format_exc()
            log_debug(f"HANDLER ERROR: {str(e)}", "ERROR")
            log_debug(f"HANDLER TRACEBACK:\n{error_details}", "ERROR")

            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            error_response = json.dumps(
                {
                    "error": str(e),
                    "traceback": error_details,
                    "path": getattr(self, "path", "unknown"),
                }
            )
            self.wfile.write(error_response.encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
