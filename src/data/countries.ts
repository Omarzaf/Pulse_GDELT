export interface AtlasCountry {
  iso3: string;
  name: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export const ATLAS_COUNTRIES: AtlasCountry[] = [
  { iso3: "USA", name: "United States", x: 90, y: 115, width: 118, height: 58 },
  { iso3: "BRA", name: "Brazil", x: 205, y: 235, width: 78, height: 92 },
  { iso3: "FRA", name: "France", x: 395, y: 135, width: 45, height: 38 },
  { iso3: "GBR", name: "United Kingdom", x: 372, y: 112, width: 38, height: 34 },
  { iso3: "COD", name: "Democratic Republic of the Congo", x: 438, y: 248, width: 72, height: 70 },
  { iso3: "KEN", name: "Kenya", x: 516, y: 247, width: 47, height: 48 },
  { iso3: "IND", name: "India", x: 650, y: 210, width: 72, height: 62 },
  { iso3: "CHN", name: "China", x: 690, y: 142, width: 118, height: 72 },
  { iso3: "JPN", name: "Japan", x: 850, y: 155, width: 34, height: 58 },
  { iso3: "AUS", name: "Australia", x: 765, y: 322, width: 116, height: 62 }
];

export function countryNameForIso3(iso3: string | null): string {
  return ATLAS_COUNTRIES.find((country) => country.iso3 === iso3)?.name ?? "No country selected";
}
