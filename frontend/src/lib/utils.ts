import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

export function getRiskColor(level: string): string {
  const colors: Record<string, string> = {
    low: "bg-green-500",
    medium: "bg-yellow-500",
    high: "bg-orange-500",
    critical: "bg-red-500",
  };
  return colors[level.toLowerCase()] || "bg-gray-500";
}

export function getRiskLabel(level: string): string {
  const labels: Record<string, string> = {
    low: "Low Risk",
    medium: "Medium Risk",
    high: "High Risk",
    critical: "Critical Risk",
  };
  return labels[level.toLowerCase()] || "Unknown Risk";
}

export function getConfidenceLabel(confidence: number): string {
  if (confidence >= 0.9) return "High Confidence";
  if (confidence >= 0.7) return "Medium Confidence";
  return "Low Confidence";
}