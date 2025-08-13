"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Search, Building, ExternalLink, Tag } from "@/components/ui/icons";
import { cn } from "@/lib/utils";

interface CompanyMaster {
  id?: string;
  name: string;
  websiteUrl?: string;
  wikipediaUrl?: string;
  linkedinUrl?: string;
  logoUrl?: string;
  description?: string;
  industry?: string;
  tagsMaster: string[];
  naicsCode?: string;
  stillInBusiness?: boolean;
}

interface SimilarCompanyResult {
  company: CompanyMaster;
  justification: string;
}

interface CompanySearchResponse {
  inputCompany: {
    name: string;
    personalNote: string;
    tags: string;
  };
  similarCompanies: SimilarCompanyResult[];
}

export default function CompanySearch() {
  const [formData, setFormData] = useState({
    name: "",
    personalNote: "",
    tags: "",
  });
  const [results, setResults] = useState<CompanySearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiEndpoint = process.env.NODE_ENV === 'development' 
    ? "http://localhost:8080/search-companies"
    : "/api/search-companies";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim() || !formData.personalNote.trim() || !formData.tags.trim()) {
      setError("Please fill in all fields");
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await fetch(apiEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({})) as any;
        const errorMessage = errorData?.detail?.error || 
                           errorData?.detail || 
                           errorData?.error || 
                           `Search failed (${response.status})`;
        throw new Error(errorMessage);
      }

      const data: CompanySearchResponse = await response.json();
      setResults(data);
    } catch (err) {
      console.error("Search error:", err);
      setError(err instanceof Error ? err.message : "An error occurred while searching");
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof typeof formData) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setFormData(prev => ({ ...prev, [field]: e.target.value }));
  };

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] max-w-6xl mx-auto bg-background border border-border rounded-lg shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-muted/30">
        <div className="flex items-center gap-2">
          <Building size={24} className="text-primary" />
          <h1 className="text-lg font-semibold">Company Search</h1>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <div className={cn(
            "w-2 h-2 rounded-full",
            loading ? "bg-yellow-500" : "bg-green-500"
          )} />
          {loading ? "Searching..." : "Ready"}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="p-6">
          {/* Search Form */}
          <form onSubmit={handleSubmit} className="space-y-4 mb-8">
            <div className="grid md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label htmlFor="name" className="text-sm font-medium">
                  Company Name *
                </label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={handleInputChange("name")}
                  placeholder="e.g., Tesla"
                  disabled={loading}
                  required
                />
              </div>
              
              <div className="space-y-2">
                <label htmlFor="tags" className="text-sm font-medium">
                  Tags *
                </label>
                <Input
                  id="tags"
                  value={formData.tags}
                  onChange={handleInputChange("tags")}
                  placeholder="e.g., electric vehicles, sustainability, technology"
                  disabled={loading}
                  required
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <label htmlFor="personalNote" className="text-sm font-medium">
                Personal Note *
              </label>
              <Textarea
                id="personalNote"
                value={formData.personalNote}
                onChange={handleInputChange("personalNote")}
                placeholder="Describe what makes this company interesting to you..."
                className="min-h-[100px]"
                disabled={loading}
                required
              />
            </div>

            <Button type="submit" disabled={loading} className="w-full md:w-auto">
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
                  Searching...
                </>
              ) : (
                <>
                  <Search size={16} className="mr-2" />
                  Find Similar Companies
                </>
              )}
            </Button>
          </form>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          {/* Results */}
          {results && (
            <div className="space-y-6">
              {/* Input Company Display */}
              <div className="p-4 bg-muted/20 rounded-lg border border-border">
                <h2 className="text-lg font-semibold mb-3">Your Company</h2>
                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <span className="text-sm font-medium text-muted-foreground">Name:</span>
                    <p className="font-medium">{results.inputCompany.name}</p>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-muted-foreground">Tags:</span>
                    <p className="text-sm">{results.inputCompany.tags}</p>
                  </div>
                  <div className="md:col-span-1">
                    <span className="text-sm font-medium text-muted-foreground">Personal Note:</span>
                    <p className="text-sm">{results.inputCompany.personalNote}</p>
                  </div>
                </div>
              </div>

              {/* Similar Companies */}
              <div>
                <h2 className="text-lg font-semibold mb-4">Similar Companies ({results.similarCompanies.length})</h2>
                <div className="grid gap-4">
                  {results.similarCompanies.map((item, index) => (
                    <div key={index} className="border border-border rounded-lg p-4 bg-background">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Building size={20} className="text-primary flex-shrink-0 mt-0.5" />
                          <h3 className="font-semibold text-lg">{item.company.name}</h3>
                        </div>
                        <div className="flex items-center gap-2">
                          {item.company.stillInBusiness !== undefined && (
                            <span className={cn(
                              "px-2 py-1 text-xs rounded-full",
                              item.company.stillInBusiness === true
                                ? "bg-green-100 text-green-800" 
                                : item.company.stillInBusiness === false
                                ? "bg-red-100 text-red-800"
                                : "bg-gray-100 text-gray-800"
                            )}>
                              {item.company.stillInBusiness === true 
                                ? "Active" 
                                : item.company.stillInBusiness === false 
                                ? "Inactive" 
                                : "Unknown"}
                            </span>
                          )}
                          {item.company.industry && (
                            <span className="px-2 py-1 bg-primary/10 text-primary text-xs rounded-full">
                              {item.company.industry}
                            </span>
                          )}
                        </div>
                      </div>

                      {item.company.description && (
                        <p className="text-muted-foreground mb-3">{item.company.description}</p>
                      )}

                      {/* Tags */}
                      {item.company.tagsMaster.length > 0 && (
                        <div className="flex items-center gap-1 mb-3 flex-wrap">
                          <Tag size={14} className="text-muted-foreground" />
                          {item.company.tagsMaster.map((tag, tagIndex) => (
                            <span key={tagIndex} className="px-2 py-1 bg-muted text-muted-foreground text-xs rounded">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Links */}
                      <div className="flex items-center gap-4 mb-3 flex-wrap">
                        {item.company.websiteUrl && (
                          <a
                            href={item.company.websiteUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-primary hover:underline flex items-center gap-1"
                          >
                            <ExternalLink size={12} />
                            Website
                          </a>
                        )}
                        {item.company.linkedinUrl && (
                          <a
                            href={item.company.linkedinUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-primary hover:underline flex items-center gap-1"
                          >
                            <ExternalLink size={12} />
                            LinkedIn
                          </a>
                        )}
                        {item.company.wikipediaUrl && (
                          <a
                            href={item.company.wikipediaUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-primary hover:underline flex items-center gap-1"
                          >
                            <ExternalLink size={12} />
                            Wikipedia
                          </a>
                        )}
                      </div>

                      {/* Justification */}
                      <div className="border-t border-border pt-3">
                        <p className="text-sm text-muted-foreground">
                          <span className="font-medium">Why it's similar:</span> {item.justification}
                        </p>
                      </div>

                      {/* NAICS Code */}
                      {item.company.naicsCode && (
                        <div className="text-xs text-muted-foreground mt-2">
                          NAICS: {item.company.naicsCode}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Empty State */}
          {!results && !loading && !error && (
            <div className="flex flex-col items-center justify-center py-12 text-center space-y-4">
              <Search size={48} className="text-muted-foreground" />
              <div className="space-y-2">
                <h3 className="text-lg font-medium">Find Similar Companies</h3>
                <p className="text-muted-foreground max-w-md">
                  Enter your company details above to find similar companies using AI-powered search.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}