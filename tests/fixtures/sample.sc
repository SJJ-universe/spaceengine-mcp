Star "MCP_TestStar"
{
	Class         "G2 V"
	Mass          1.0
	Radius        1.0
	Temperature   5778
	Luminosity    1.0
}

Planet "MCP_TestPlanet"
{
	ParentBody    "MCP_TestStar"
	Class         "Terra"
	Mass          1.0
	Radius        6371

	Orbit
	{
		SemiMajorAxis   1.0
		Period          1.0
		Eccentricity    0.017
		Inclination     0.0
	}
}
