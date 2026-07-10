import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/briefings";

export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      { userAgent: "*", allow: "/" },
      // 네이버 검색로봇 명시 허용
      { userAgent: "Yeti", allow: "/" },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
