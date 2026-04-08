Planet "MCP_DeepNested"
{
    ParentBody  "MCP_TestStar"
    Class       "Terra"
    Mass        1.0
    Radius      6371

    Surface
    {
        Style       0.5
        ColorMap    "Earth/Color"
        Terrain
        {
            HeightScale 10
            SnowyLine   0.8
        }
    }

    Atmosphere
    {
        Pressure    1.013
        Composition
        {
            N2      0.78
            O2      0.21
            Ar      0.009
        }
    }

    Orbit
    {
        SemiMajorAxis   1.0
        Eccentricity    0.017
        Inclination     0.0
    }
}
