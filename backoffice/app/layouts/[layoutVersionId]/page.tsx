import { GeometryEditor } from "../../../components/GeometryEditor";
import { ReviewActionPanel } from "../../../components/ReviewActionPanel";

export default function LayoutDetailPage({ params }: { params: { layoutVersionId: string } }) {
  return (
    <main>
      <h2>Layout detail: {params.layoutVersionId}</h2>
      <p>Layout version compare and lineage are displayed in this view.</p>
      <ReviewActionPanel layoutVersionId={params.layoutVersionId} />
      <GeometryEditor layoutVersionId={params.layoutVersionId} />
    </main>
  );
}
