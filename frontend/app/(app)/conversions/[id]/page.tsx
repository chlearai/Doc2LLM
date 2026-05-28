import { ConversionDetailClient } from "@/components/conversion-detail-client";

export default async function ConversionDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ConversionDetailClient id={id} />;
}
