export default function VenueDetailPage({ params }: { params: { venueId: string } }) {
  return (
    <main>
      <h2>Venue detail: {params.venueId}</h2>
      <p>Imagery inspection, crop management, extraction run detail, validation report view, publish history.</p>
    </main>
  );
}
