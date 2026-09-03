export type CityKey = "oslo" | "bergen" | "trondheim" | "stavanger" | "tromso";

export type City = {
  slug: CityKey;
  name: string;
  lat: number;
  lon: number;
  zoom: number;
};

export const CITIES: Record<CityKey, City> = {
  oslo: { slug: "oslo", name: "Oslo", lat: 59.9139, lon: 10.7522, zoom: 11 },
  bergen: { slug: "bergen", name: "Bergen", lat: 60.3913, lon: 5.3221, zoom: 11 },
  trondheim: { slug: "trondheim", name: "Trondheim", lat: 63.4305, lon: 10.3951, zoom: 11 },
  stavanger: { slug: "stavanger", name: "Stavanger", lat: 58.97, lon: 5.7331, zoom: 11 },
  tromso: { slug: "tromso", name: "Tromsø", lat: 69.6492, lon: 18.9553, zoom: 11 },
};

export const CITY_LIST = Object.values(CITIES);
