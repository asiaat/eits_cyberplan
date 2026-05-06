import { useState, useMemo } from "react";
import { useTranslation } from "@/lib/i18n";
import { terminology, Term } from "@/lib/i18n/terminology";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type SearchResult = Term & { category: string };

export default function TerminologyPage() {
  const { t } = useTranslation();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

  const categories = useMemo(() => {
    return terminology.map((cat) => ({
      key: cat.key,
      label: t(`terminology.categories.${cat.key}`),
    }));
  }, [t]);

  const isSearching = searchQuery || selectedCategory !== "all";

  const searchResults = useMemo((): SearchResult[] => {
    if (!isSearching) return [];

    const query = searchQuery.toLowerCase().trim();
    const results: SearchResult[] = [];

    const relevantCategories = selectedCategory === "all"
      ? terminology
      : terminology.filter((c) => c.key === selectedCategory);

    for (const cat of relevantCategories) {
      for (const term of cat.terms) {
        const searchText = term.et.toLowerCase();
        const englishText = term.en.toLowerCase();
        const descriptionText = term.description.toLowerCase();

        if (searchText.includes(query) || englishText.includes(query) || descriptionText.includes(query)) {
          results.push({ ...term, category: cat.key });
        }
      }
    }

    return results;
  }, [searchQuery, selectedCategory, isSearching]);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">{t("terminology.title")}</h1>
      <p className="text-muted-foreground">{t("terminology.description")}</p>

      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <Input
            type="text"
            placeholder={t("terminology.search")}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full"
          />
        </div>
        <select
          className="px-3 py-2 border rounded-md bg-background"
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
        >
          <option value="all">{t("terminology.allCategories")}</option>
          {categories.map((cat) => (
            <option key={cat.key} value={cat.key}>
              {cat.label}
            </option>
          ))}
        </select>
      </div>

      {isSearching && searchResults.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          {t("terminology.noResults")}
        </div>
      )}

      {isSearching && searchResults.length > 0 && (
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            {searchResults.length} {t("terminology.results")}
          </p>
          {searchResults.map((item, idx) => (
            <Card key={idx}>
              <CardHeader>
                <div className="flex justify-between items-start gap-4">
                  <CardTitle className="text-lg">{item.et}</CardTitle>
                  <span className="text-sm text-muted-foreground shrink-0">
                    {item.en}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{item.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {!isSearching && (
        <div className="space-y-8">
          {terminology.map((cat) => (
            <div key={cat.key}>
              <h2 className="text-xl font-semibold mb-4">
                {t(`terminology.categories.${cat.key}`)}
              </h2>
              <div className="grid gap-4">
                {cat.terms.map((term, idx) => (
                  <Card key={idx}>
                    <CardHeader>
                      <div className="flex justify-between items-start gap-4">
                        <CardTitle className="text-lg">{term.et}</CardTitle>
                        <span className="text-sm text-muted-foreground shrink-0">
                          {term.en}
                        </span>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground">{term.description}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}