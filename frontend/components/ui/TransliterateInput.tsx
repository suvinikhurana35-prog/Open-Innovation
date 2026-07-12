"use client";

import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { useI18n } from "@/lib/i18n";

const TRANSLITERATE_API =
  process.env.NEXT_PUBLIC_API_URL
    ? `${process.env.NEXT_PUBLIC_API_URL}/api/transliterate`
    : "http://localhost:8000/api/transliterate";

const LANG_LABELS: Record<string, string> = {
  hi: "अ",
  bn: "অ",
  ta: "அ",
  en: "A",
};

interface Props {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  placeholder?: string;
  className?: string;
}

export function TransliterateInput({ value, onChange, onSubmit, placeholder, className = "" }: Props) {
  const { lang } = useI18n();
  const [enabled, setEnabled] = useState(lang !== "en");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [currentWord, setCurrentWord] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-enable when language changes to a non-English language
  useEffect(() => {
    setEnabled(lang !== "en");
  }, [lang]);

  const fetchSuggestions = async (word: string) => {
    if (!word || lang === "en") {
      setSuggestions([]);
      return;
    }
    try {
      const res = await fetch(TRANSLITERATE_API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: word, language: lang }),
      });
      if (!res.ok) return;
      const data = await res.json();
      setSuggestions(data.suggestions || []);
    } catch {
      setSuggestions([]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    onChange(raw);

    if (!enabled) return;

    // Extract the current (last) word being typed
    const words = raw.split(/\s/);
    const last = words[words.length - 1];
    setCurrentWord(last);

    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (last.length > 0) {
      debounceRef.current = setTimeout(() => fetchSuggestions(last), 300);
    } else {
      setSuggestions([]);
    }
  };

  const acceptSuggestion = (suggestion: string) => {
    const words = value.split(/\s/);
    words[words.length - 1] = suggestion;
    onChange(words.join(" ") + " ");
    setSuggestions([]);
    setCurrentWord("");
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      if (suggestions.length > 0 && currentWord) {
        e.preventDefault();
        acceptSuggestion(suggestions[0]);
        return;
      }
      e.preventDefault();
      onSubmit();
    }
    if (e.key === " " && suggestions.length > 0 && currentWord) {
      e.preventDefault();
      acceptSuggestion(suggestions[0]);
    }
    if (e.key === "Escape") {
      setSuggestions([]);
    }
  };

  return (
    <div className="relative flex-1">
      <div className="flex items-center gap-2">
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className={`flex-1 rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm shadow-sm focus:border-green-400 focus:outline-none focus:ring-2 focus:ring-green-100 ${className}`}
        />
        {lang !== "en" && (
          <button
            type="button"
            onClick={() => {
              setEnabled((p) => !p);
              setSuggestions([]);
            }}
            title={enabled ? "Transliteration ON — click to type in English" : "Transliteration OFF — click to enable"}
            className={`shrink-0 rounded-lg border px-3 py-2 text-sm font-bold transition-colors ${
              enabled
                ? "border-green-400 bg-green-50 text-green-700"
                : "border-gray-200 bg-gray-50 text-gray-500"
            }`}
          >
            {LANG_LABELS[lang] ?? "अ"}
          </button>
        )}
      </div>

      {/* Suggestions dropdown */}
      {suggestions.length > 0 && enabled && (
        <div className="absolute bottom-full left-0 mb-1 z-50 flex flex-wrap gap-1.5 rounded-xl border border-gray-200 bg-white p-2 shadow-lg">
          {suggestions.map((s, i) => (
            <button
              key={i}
              type="button"
              onMouseDown={(e) => {
                e.preventDefault();
                acceptSuggestion(s);
              }}
              className={`rounded-lg px-3 py-1 text-sm transition-colors ${
                i === 0
                  ? "bg-green-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-green-50 hover:text-green-700"
              }`}
            >
              {s}
            </button>
          ))}
          <span className="self-center text-xs text-gray-400 ml-1">Space/↵ to accept</span>
        </div>
      )}
    </div>
  );
}

export default TransliterateInput;
