__all__ = (
    "ads_values",
    "campaigns_values",
    "keywords_values",
)

ad_copy = [
    "\nKosovo-Macedonia | Pristina-Skoplje | Search | Worldwide | EN",
    "Pristina to Skoplje Transport | Exact",
    "Exact",
    "H1 - Pristina",
    "H2 - Skoplje",
    "Rezerviraj odmah",
    "Rezerviraj odmah 2",
    "Rezerviraj odmah 3",
    "Rezerviraj odmah 4",
    "Rezerviraj odmah 5",
    "Rezerviraj odmah 6",
    "Rezerviraj odmah 7",
    "Rezerviraj odmah 8",
    "Rezerviraj odmah 9",
    "Rezerviraj odmah 10",
    "Rezerviraj odmah 11",
    "Rezerviraj odmah 12",
    "Rezerviraj odmah 13",
    "Povezujemo više od 80 država i preko 20.000 gradova",
    "Preko 1500 sniženih karata Iskoristite popuste do 50%",
    "Preko 1500 sniženih karata Iskoristite popuste do 60%",
    "Preko 1500 sniženih karata Iskoristite popuste do 70%",
    "Pristina",
    "Skoplje",
    "getbybus.com/en/pristina-skoplje",
]

ads_values = {
    "values": [
        [
            "Campaign Name",
            "Ad Group Name",
            "Match Type",
            "Headline 1",
            "Headline 2",
            "Headline 3",
            "Headline 4",
            "Headline 5",
            "Headline 6",
            "Headline 7",
            "Headline 8",
            "Headline 9",
            "Headline 10",
            "Headline 11",
            "Headline 12",
            "Headline 13",
            "Headline 14",
            "Headline 15",
            "Description Line 1",
            "Description Line 2",
            "Description Line 3",
            "Description Line 4",
            "Path 1",
            "Path 2",
            "Final URL",
        ],
        ad_copy,
        ad_copy,  # Duplicate ad
    ]
}


campaign_1 = [
    "\nCroatia | Ancona-Split | Search | Croatia | EN",
    "EN",
    "10",
    "TRUE",
    "TRUE",
    "All Departures Here",
    "Affordable Bus Tickets",
    "GetByBus",
    "Hassle-Free Booking",
    "Free cancellation",
    "Professional Support",
    "Return tickets",
    "Reservation",
    "",
    "0.3",
    "",
    "",
    "",
    "Croatia",
    None,
    None,
    None,
    None,
    None,
]
campaign_2 = [
    "netherlands | Eindhoven-Amsterdam | Search | Worldwide | EN",
    "EN",
    "10",
    "TRUE",
    "TRUE",
    "All Departures Here",
    "Affordable Bus Tickets",
    "GetByBus",
    "Hassle-Free Booking",
    "Free cancellation",
    "Professional Support",
    "Return tickets",
    "Reservation",
    "",
    "0.3",
    "",
    "",
    "",
    "Croatia",
    None,
    None,
    None,
    None,
    None,
]
campaigns_values = {
    "values": [
        [
            "Campaign Name",
            "Language Code",
            "Campaign Budget",
            "Search Network",
            "Google Search Network",
            "Sitelink 1",
            "Sitelink 2",
            "Sitelink 3",
            "Sitelink 4",
            "Callout 1",
            "Callout 2",
            "Callout 3",
            "Callout 4",
            "Callout 5",
            "Default max. CPC",
            "Target Language 1",
            "Target Language 2",
            "Target Language 3",
            "Include Location 1",
            "Include Location 2",
            "Include Location 3",
            "Exclude Location 1",
            "Exclude Location 2",
            "Exclude Location 3",
        ],
        campaign_1,
    ]
}

keywords_values = {
    "values": [
        [
            "Campaign Name",
            "Ad Group Name",
            "Match Type",
            "Keyword",
            "Level",
            "Negative",
        ],
        [
            "\nKosovo-Macedonia | Pristina-Skoplje | Search | Worldwide | EN",
            "Pristina to Skoplje Transport | Exact",
            "Exact",
            "Svi autobusni polasci",
            None,
            "FALSE",
        ],
        [
            "\nKosovo-Macedonia | Pristina-Skoplje | Search | Worldwide | EN",
            "Pristina to Skoplje Transport | Exact",
            "Exact",
            "Rezerviraj odmah",
            None,
            "FALSE",
        ],
        [
            "\nKosovo-Macedonia | Pristina-Skoplje | Search | Worldwide | EN",
            "Pristina to Skoplje Transport | Exact",
            "Exact",
            "Neg Ad Group",
            "Ad Group",
            "TRUE",
        ],
        [
            "\nKosovo-Macedonia | Pristina-Skoplje | Search | Worldwide | EN",
            None,
            "Exact",
            "Neg Campaign",
            "Campaign",
            "TRUE",
        ],
    ]
}
