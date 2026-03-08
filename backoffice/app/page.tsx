import Link from "next/link";

export default function HomePage() {
  return (
    <main>
      <h1>TrackReco Backoffice</h1>
      <ul>
        <li><Link href="/venues">Venue list</Link></li>
        <li><Link href="/jobs">Job monitoring</Link></li>
      </ul>
    </main>
  );
}
