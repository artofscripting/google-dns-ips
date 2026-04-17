"""Example usage for the google_dns_ips library."""

from google_dns_ips import GoogleIPQuery, get_google_ip_cidrs


def main() -> None:
    result = get_google_ip_cidrs()
    query = GoogleIPQuery.from_cidrs(result.cidrs)

    print(f"Visited TXT records: {len(result.visited_records)}")
    for name in result.visited_records:
        print(f"  - {name}")

    print(f"\nResolved CIDRs: {len(result.cidrs)}")
    for cidr in result.cidrs:
        print(cidr)

    print("\nMembership and overlap checks:")
    checks = (
        "8.8.8.8",
        "8.8.8.0/24",
        "8.8.0.0-8.8.255.255",
        "1.1.1.1",
    )
    for value in checks:
        contains = query.contains(value)
        collides = query.collides(value)
        print(f"{value}: contains={contains}, collides={collides}")


if __name__ == "__main__":
    main()
