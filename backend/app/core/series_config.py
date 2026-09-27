"""Configuration of all 18 Macro Series for Phase 1 as specified in Section 5 of methodology."""

SERIES_CATALOG = [
    # Growth
    {
        "fred_series_id": "GDPC1",
        "name": "Real Gross Domestic Product",
        "category": "growth",
        "description": "Real GDP in billions of chained 2017 dollars",
        "frequency": "quarterly",
        "unit": "billions",
        "seasonally_adjusted": True,
    },
    {
        "fred_series_id": "INDPRO",
        "name": "Industrial Production Index",
        "category": "growth",
        "description": "Real output of manufacturing, mining, and electric/gas utilities",
        "frequency": "monthly",
        "unit": "index",
        "seasonally_adjusted": True,
    },
    {
        "fred_series_id": "RSAFS",
        "name": "Advance Real Retail Sales",
        "category": "growth",
        "description": "Retail and food services sales",
        "frequency": "monthly",
        "unit": "millions",
        "seasonally_adjusted": True,
    },
    {
        "fred_series_id": "UNRATE",
        "name": "Civilian Unemployment Rate",
        "category": "growth",
        "description": "Unemployment rate percentage of total civilian labor force",
        "frequency": "monthly",
        "unit": "percent",
        "seasonally_adjusted": True,
    },
    {
        "fred_series_id": "ICSA",
        "name": "Initial Jobless Claims",
        "category": "growth",
        "description": "Weekly initial claims for unemployment insurance",
        "frequency": "weekly",
        "unit": "number",
        "seasonally_adjusted": True,
    },
    {
        "fred_series_id": "UMCSENT",
        "name": "Consumer Sentiment",
        "category": "growth",
        "description": "University of Michigan Consumer Sentiment Index",
        "frequency": "monthly",
        "unit": "index",
        "seasonally_adjusted": False,
    },
    # Inflation
    {
        "fred_series_id": "CPIAUCSL",
        "name": "Consumer Price Index (CPI)",
        "category": "inflation",
        "description": "CPI for All Urban Consumers: All Items",
        "frequency": "monthly",
        "unit": "index",
        "seasonally_adjusted": True,
    },
    {
        "fred_series_id": "CPILFESL",
        "name": "Core CPI",
        "category": "inflation",
        "description": "CPI for All Urban Consumers: Less Food and Energy",
        "frequency": "monthly",
        "unit": "index",
        "seasonally_adjusted": True,
    },
    {
        "fred_series_id": "PCEPI",
        "name": "PCE Price Index",
        "category": "inflation",
        "description": "Personal Consumption Expenditures Chain-type Price Index",
        "frequency": "monthly",
        "unit": "index",
        "seasonally_adjusted": True,
    },
    {
        "fred_series_id": "PCEPILFE",
        "name": "Core PCE Price Index",
        "category": "inflation",
        "description": "Personal Consumption Expenditures Less Food and Energy",
        "frequency": "monthly",
        "unit": "index",
        "seasonally_adjusted": True,
    },
    # Interest Rates
    {
        "fred_series_id": "FEDFUNDS",
        "name": "Federal Funds Effective Rate",
        "category": "rates",
        "description": "Federal Funds Effective Rate",
        "frequency": "monthly",
        "unit": "percent",
        "seasonally_adjusted": False,
    },
    {
        "fred_series_id": "DGS2",
        "name": "2-Year Treasury Yield",
        "category": "rates",
        "description": "2-Year Treasury Constant Maturity Rate",
        "frequency": "daily",
        "unit": "percent",
        "seasonally_adjusted": False,
    },
    {
        "fred_series_id": "DGS10",
        "name": "10-Year Treasury Yield",
        "category": "rates",
        "description": "10-Year Treasury Constant Maturity Rate",
        "frequency": "daily",
        "unit": "percent",
        "seasonally_adjusted": False,
    },
    {
        "fred_series_id": "DGS30",
        "name": "30-Year Treasury Yield",
        "category": "rates",
        "description": "30-Year Treasury Constant Maturity Rate",
        "frequency": "daily",
        "unit": "percent",
        "seasonally_adjusted": False,
    },
    {
        "fred_series_id": "DFII10",
        "name": "10-Year Real Yield (TIPS)",
        "category": "rates",
        "description": "10-Year Treasury Inflation-Indexed Security Constant Maturity",
        "frequency": "daily",
        "unit": "percent",
        "seasonally_adjusted": False,
    },
    {
        "fred_series_id": "T10Y2Y",
        "name": "10-Year Treasury Minus 2-Year Treasury Spread",
        "category": "rates",
        "description": "10-Year Treasury Constant Maturity Minus 2-Year Treasury Constant Maturity (Yield Curve Spread)",
        "frequency": "daily",
        "unit": "percent",
        "seasonally_adjusted": False,
    },
    {
        "fred_series_id": "SAHMREALTIME",
        "name": "Sahm Rule Recession Indicator",
        "category": "growth",
        "description": "Real-time Sahm Rule Recession Indicator (Difference between 3-month MA unemployment and 12-month low)",
        "frequency": "monthly",
        "unit": "percent",
        "seasonally_adjusted": True,
    },
    # Liquidity
    {
        "fred_series_id": "M2SL",
        "name": "M2 Money Supply",
        "category": "liquidity",
        "description": "M2 Money Stock",
        "frequency": "monthly",
        "unit": "billions",
        "seasonally_adjusted": True,
    },
    {
        "fred_series_id": "WALCL",
        "name": "Fed Total Assets",
        "category": "liquidity",
        "description": "Assets: Total Assets (Less Eliminations from Consolidation)",
        "frequency": "weekly",
        "unit": "millions",
        "seasonally_adjusted": False,
    },
    # Credit & Risk
    {
        "fred_series_id": "VIXCLS",
        "name": "CBOE Volatility Index (VIX)",
        "category": "risk",
        "description": "CBOE Volatility Index",
        "frequency": "daily",
        "unit": "index",
        "seasonally_adjusted": False,
    },
    {
        "fred_series_id": "BAMLH0A0HYM2",
        "name": "High Yield Option-Adjusted Spread",
        "category": "credit",
        "description": "ICE BofA US High Yield Index Option-Adjusted Spread",
        "frequency": "daily",
        "unit": "percent",
        "seasonally_adjusted": False,
    },
    # Additional Growth Indicators
    {
        "fred_series_id": "PAYEMS",
        "name": "Total Nonfarm Payrolls",
        "category": "growth",
        "description": "Total nonfarm payroll employment in thousands of persons",
        "frequency": "monthly",
        "unit": "thousands",
        "seasonally_adjusted": True,
    },
    {
        "fred_series_id": "JTSJOL",
        "name": "JOLTS Job Openings",
        "category": "growth",
        "description": "Job Openings: Total Nonfarm",
        "frequency": "monthly",
        "unit": "thousands",
        "seasonally_adjusted": True,
    },
    {
        "fred_series_id": "JTSQUR",
        "name": "Quits Rate",
        "category": "growth",
        "description": "Quits Rate: Total Nonfarm",
        "frequency": "monthly",
        "unit": "percent",
        "seasonally_adjusted": True,
    },
    {
        "fred_series_id": "CES0500000003",
        "name": "Average Hourly Earnings",
        "category": "growth",
        "description": "Average Hourly Earnings of All Employees, Total Private",
        "frequency": "monthly",
        "unit": "dollars",
        "seasonally_adjusted": True,
    },
    {
        "fred_series_id": "HOUST",
        "name": "Housing Starts",
        "category": "growth",
        "description": "Housing Starts: Total New Privately Owned Housing Units Started",
        "frequency": "monthly",
        "unit": "thousands",
        "seasonally_adjusted": True,
    },
    {
        "fred_series_id": "PERMIT",
        "name": "Building Permits",
        "category": "growth",
        "description": "New Privately-Owned Housing Units Authorized in Permit-Issuing Places",
        "frequency": "monthly",
        "unit": "thousands",
        "seasonally_adjusted": True,
    },
    {
        "fred_series_id": "DGORDER",
        "name": "Durable Goods Orders",
        "category": "growth",
        "description": "Manufacturers' New Orders: Durable Goods",
        "frequency": "monthly",
        "unit": "millions",
        "seasonally_adjusted": True,
    },
    {
        "fred_series_id": "GACDFSA066MSFRBPHI",
        "name": "Philly Fed Manufacturing Index",
        "category": "growth",
        "description": "Philadelphia Fed Diffusion Index of General Business Conditions",
        "frequency": "monthly",
        "unit": "index",
        "seasonally_adjusted": True,
    },
    {
        "fred_series_id": "GACDISA066MSFRBNY",
        "name": "NY Empire State Manufacturing Index",
        "category": "growth",
        "description": "Empire State Manufacturing Survey General Business Conditions Index",
        "frequency": "monthly",
        "unit": "index",
        "seasonally_adjusted": True,
    },
    {
        "fred_series_id": "CSUSHPINSA",
        "name": "Case-Shiller Home Price Index",
        "category": "growth",
        "description": "S&P CoreLogic Case-Shiller U.S. National Home Price Index",
        "frequency": "monthly",
        "unit": "index",
        "seasonally_adjusted": False,
    },
    # Additional Inflation Indicators
    {
        "fred_series_id": "T5YIFR",
        "name": "5Y5Y Forward Inflation Expectation",
        "category": "inflation",
        "description": "5-Year, 5-Year Forward Inflation Expectation Rate",
        "frequency": "daily",
        "unit": "percent",
        "seasonally_adjusted": False,
    },
    {
        "fred_series_id": "T10YIE",
        "name": "10-Year Breakeven Inflation Rate",
        "category": "inflation",
        "description": "10-Year Breakeven Inflation Rate",
        "frequency": "daily",
        "unit": "percent",
        "seasonally_adjusted": False,
    },
    {
        "fred_series_id": "PPIFIS",
        "name": "PPI Final Demand",
        "category": "inflation",
        "description": "Producer Price Index by Commodity: Final Demand",
        "frequency": "monthly",
        "unit": "index",
        "seasonally_adjusted": True,
    },
    # Additional Liquidity Indicators & Derived
    {
        "fred_series_id": "WTREGEN",
        "name": "Treasury General Account (TGA)",
        "category": "liquidity",
        "description": "Treasury General Account Operating Balance",
        "frequency": "daily",
        "unit": "millions",
        "seasonally_adjusted": False,
    },
    {
        "fred_series_id": "RRPONTSYD",
        "name": "Overnight Reverse Repo (ON RRP)",
        "category": "liquidity",
        "description": "Overnight Reverse Repurchase Agreements: Treasury Securities Awarded",
        "frequency": "daily",
        "unit": "billions",
        "seasonally_adjusted": False,
    },
    {
        "fred_series_id": "FED_NET_LIQUIDITY",
        "name": "Fed Net Liquidity",
        "category": "liquidity",
        "description": "Derived Fed Net Liquidity = WALCL (Assets) - TGA - ON RRP",
        "frequency": "weekly",
        "unit": "billions",
        "seasonally_adjusted": False,
    },
    {
        "fred_series_id": "NFCI",
        "name": "Chicago Fed Financial Conditions Index",
        "category": "credit",
        "description": "Chicago Fed National Financial Conditions Index (NFCI)",
        "frequency": "weekly",
        "unit": "index",
        "seasonally_adjusted": False,
    },
    {
        "fred_series_id": "STLFSI4",
        "name": "St. Louis Fed Financial Stress Index",
        "category": "credit",
        "description": "St. Louis Fed Financial Stress Index Version 4",
        "frequency": "weekly",
        "unit": "index",
        "seasonally_adjusted": False,
    },
    # Additional Risk & Commodity Indicators
    {
        "fred_series_id": "DCOILWTICO",
        "name": "WTI Crude Oil Price",
        "category": "risk",
        "description": "Crude Oil Prices: West Texas Intermediate (WTI)",
        "frequency": "daily",
        "unit": "dollars",
        "seasonally_adjusted": False,
    },
    {
        "fred_series_id": "PCOPPUSDM",
        "name": "Global Copper Price",
        "category": "risk",
        "description": "Global price of Copper in U.S. Dollars per Metric Ton",
        "frequency": "monthly",
        "unit": "dollars",
        "seasonally_adjusted": False,
    },
    {
        "fred_series_id": "IQ12260",
        "name": "Nonmonetary Gold Price Index",
        "category": "benchmark",
        "description": "Export Price Index (End Use): Nonmonetary Gold",
        "frequency": "monthly",
        "unit": "index",
        "seasonally_adjusted": False,
    },
    {
        "fred_series_id": "COPPER_GOLD",
        "name": "Copper / Gold Ratio",
        "category": "risk",
        "description": "Derived Copper to Gold Price Ratio (Global Copper / London Gold)",
        "frequency": "monthly",
        "unit": "ratio",
        "seasonally_adjusted": False,
    },
    # Benchmarks
    {
        "fred_series_id": "SP500",
        "name": "S&P 500 Index",
        "category": "benchmark",
        "description": "S&P 500 Stock Market Index",
        "frequency": "daily",
        "unit": "index",
        "seasonally_adjusted": False,
    },
    {
        "fred_series_id": "NASDAQCOM",
        "name": "Nasdaq Composite Index",
        "category": "benchmark",
        "description": "Nasdaq Composite Index",
        "frequency": "daily",
        "unit": "index",
        "seasonally_adjusted": False,
    },
    {
        "fred_series_id": "DTWEXBGS",
        "name": "U.S. Dollar Index",
        "category": "benchmark",
        "description": "Trade Weighted U.S. Dollar Index: Broad, Goods and Services",
        "frequency": "daily",
        "unit": "index",
        "seasonally_adjusted": False,
    },
    {
        "fred_series_id": "USREC",
        "name": "NBER Recession Indicator",
        "category": "benchmark",
        "description": "NBER Business Cycle Recession Indicator (1 = Recession, 0 = Expansion)",
        "frequency": "monthly",
        "unit": "binary",
        "seasonally_adjusted": False,
    },
]


def get_analytical_metadata(series_id: str, name: str, category: str, description: str = None) -> dict:
    id_upper = (series_id or "").upper()
    cat_lower = (category or "").lower()

    overview = description if description and len(description) > 20 else f"{name} ({series_id}) is a key {cat_lower} macroeconomic series from the Federal Reserve Bank of St. Louis catalog, providing real-time data to evaluate business cycles and market regimes."
    rising = "Elevates upward momentum in its core economic dimension, influencing benchmark valuations and central bank policy expectations."
    falling = "Signals deceleration in its underlying dimension, shifting capital toward defensive assets and market safety."

    # Category defaults
    if cat_lower == "rates":
        rising = "Higher yields elevate discount rates, raise corporate borrowing costs, compress growth stock P/E multiples, and strengthen currency dynamics."
        falling = "Falling yields lower capital costs, expand equity valuation multiples, support real estate activity, and lower fixed-income yields."
    elif cat_lower == "inflation":
        rising = "Elevated inflation pressures central banks toward hawkish policy tightening, eroding real purchasing power and pressuring bond prices."
        falling = "Disinflationary trends enable dovish monetary easing, supporting valuation expansion across growth assets and credit."
    elif cat_lower == "growth":
        rising = "Robust economic expansion drives corporate revenue growth, employment gains, and outperformance in cyclical equity sectors."
        falling = "Slowing growth signals macroeconomic cooling, compressing corporate earnings growth and favoring defensive asset allocation."
    elif cat_lower == "liquidity":
        rising = "Liquidity expansion expands central bank reserves and broad liquidity, driving risk asset inflation and multiple expansion."
        falling = "Liquidity contraction drains capital from financial markets, elevating asset price volatility and drawdown risk."
    elif cat_lower == "credit":
        rising = "Widening credit spreads reflect heightened corporate default risks, tightening lending standards, and risk-off sentiment."
        falling = "Tightening credit spreads indicate corporate financial health, low default expectations, and robust credit market liquidity."
    elif cat_lower == "risk":
        rising = "Spikes in market volatility or risk metrics signal investor risk-aversion, liquidity contractions, and flight to safe-haven assets."
        falling = "Subdued volatility reflects market stability, constructive risk appetite, and steady equity market appreciation."

    # Indicator specific overrides
    if id_upper == "FED_NET_LIQUIDITY":
        overview = "Fed Net Liquidity is calculated as Federal Reserve Total Assets (WALCL) minus Treasury General Account (WTREGEN) minus Overnight Reverse Repo (RRPONTSYD). It isolates unencumbered commercial bank reserves floating in capital markets."
        rising = "Expands bank reserves and market liquidity, fueling equity P/E multiple expansion, crypto rallies, and credit spread tightening."
        falling = "Drains systemic bank reserves, restricting financial market capacity, increasing drawdown risk, and elevating market volatility."
    elif id_upper == "SAHMREALTIME":
        overview = "The Real-Time Sahm Rule Recession Indicator signals the onset of a recession when the 3-month moving average of national unemployment rises by 0.50 percentage points or more relative to its minimum 3-month average over the prior 12 months."
        rising = "Breaching the 0.50% threshold confirms a macroeconomic contraction, triggering rapid Fed rate cuts, steepening yield curves, and defensive equity rotation."
        falling = "Remaining below 0.50% signals labor market resilience, solid economic expansion, and low immediate recession probability."
    elif id_upper == "COPPER_GOLD":
        overview = "The Copper to Gold Ratio divides global industrial copper prices by gold spot prices. Copper reflects industrial manufacturing demand, while gold reflects safe-haven demand, producing a pure market-based growth indicator."
        rising = "Signals economic expansion, rising global industrial activity, higher 10Y Treasury yields, and outperformance of cyclical equities over defensives."
        falling = "Indicates slowing industrial growth or stagflation fears, driving capital into Treasuries and safe-haven assets."
    elif id_upper == "NFCI":
        overview = "The Chicago Fed National Financial Conditions Index (NFCI) synthesizes 105 financial indicators tracking money market, debt, equity, and shadow banking conditions into a single composite index."
        rising = "Values above zero indicate tighter-than-average financial conditions, elevating corporate borrowing costs and constraining credit growth."
        falling = "Values below zero indicate loose financial conditions, lower cost of capital, and a supportive environment for corporate borrowing and risk-taking."
    elif id_upper == "STLFSI4":
        overview = "The St. Louis Fed Financial Stress Index Version 4 measures financial market stress across 18 weekly series including interest rates, yield spreads, and volatility indicators."
        rising = "Values above zero signal acute market distress, liquidity fragmentation, credit risk aversion, and heightened systemic risk."
        falling = "Values below zero indicate benign market stress, stable banking operations, and supportive conditions for equity risk premiums."
    elif id_upper == "GACDFSA066MSFRBPHI":
        overview = "The Philadelphia Fed Diffusion Index measures mid-Atlantic manufacturing activity. Readings above zero indicate business expansion; readings below zero indicate contraction."
        rising = "Signals regional industrial acceleration, expanding factory order backlogs, and positive momentum for nationwide ISM Manufacturing."
        falling = "Portends industrial slowdown, contracting factory output, and deferred corporate capital expenditures."
    elif id_upper == "GACDISA066MSFRBNY":
        overview = "The Empire State Manufacturing Survey measures general business conditions across New York State manufacturers, serving as the first regional Fed survey released each month."
        rising = "Signals strengthening factory orders, improving delivery times, and positive early momentum for national manufacturing."
        falling = "Signals regional manufacturing contraction, inventory destocking, and cooling industrial demand."
    elif id_upper == "CES0500000003":
        overview = "Average Hourly Earnings measures average pay for all private nonfarm employees, serving as the primary metric for tracking wage growth momentum and labor cost pressure."
        rising = "Boosts consumer purchasing power but accelerates wage-push inflation concerns, forcing central banks to maintain higher policy rates."
        falling = "Eases unit labor cost pressures and headline inflation, enabling monetary policy rate cuts."
    elif id_upper == "CSUSHPINSA":
        overview = "The Case-Shiller U.S. National Home Price Index tracks repeat-sale values of single-family housing across key metropolitan areas nationwide."
        rising = "Expands household wealth effect and home equity collateral, but erodes housing affordability for first-time buyers."
        falling = "Impairs residential real estate equity values and consumer confidence, but improves long-term housing affordability."
    elif id_upper == "HOUST":
        overview = "Housing Starts measures total new privately owned residential housing units started each month, serving as a primary gauge of physical real estate investment."
        rising = "Drives construction employment, building material demand, and durable home goods spending across the economy."
        falling = "Signals residential investment drag, tighter mortgage conditions, and broader economic cooling."
    elif id_upper == "PERMIT":
        overview = "Building Permits tracks new privately owned housing units authorized by local permit-issuing places across the United States."
        rising = "Premier leading indicator of future residential construction, signaling builder confidence and credit availability."
        falling = "Early warning signal of housing slowdown, reduced future construction payrolls, and macroeconomic deceleration."
    elif id_upper == "DGORDER":
        overview = "Durable Goods Orders measures manufacturer orders for long-lasting capital goods (machinery, electronics, heavy equipment), reflecting business investment sentiment."
        rising = "Signals strong corporate capital expenditure (CapEx) commitment, manufacturing expansion, and business confidence."
        falling = "Reflects corporate investment caution, deferred capital equipment spending, and contracting factory order backlogs."
    elif id_upper == "T5YIFR":
        overview = "The 5-Year, 5-Year Forward Inflation Expectation Rate measures expected average inflation over the 5-year period starting five years from today, derived from TIPS yields."
        rising = "Signals unanchoring inflation expectations, driving bond yield sell-offs and forcing hawkish central bank tightening."
        falling = "Indicates anchored or disinflationary long-term expectations, supporting fixed income asset valuations."
    elif id_upper == "T10YIE":
        overview = "The 10-Year Breakeven Inflation Rate represents market-implied average annual inflation expected over the next decade (10Y Nominal Treasuries minus 10Y TIPS)."
        rising = "Reflects rising inflation premiums, benefiting real assets (commodities, real estate) over fixed-rate debt."
        falling = "Signals market pricing of disinflation or recessionary demand destruction, favoring nominal Treasuries."
    elif id_upper == "WTREGEN":
        overview = "The Treasury General Account (TGA) is the U.S. Department of the Treasury’s main checking account at the Federal Reserve."
        rising = "Rebuilding the TGA absorbs commercial bank liquidity and cash reserves, creating a temporary drag on financial markets."
        falling = "Spending down the TGA injects cash liquidity directly into commercial bank reserves, boosting market risk appetite."
    elif id_upper == "RRPONTSYD":
        overview = "Overnight Reverse Repurchase Agreements (ON RRP) absorb excess cash from money market funds by offering yield directly from the Federal Reserve."
        rising = "Parks capital at the Fed, taking excess cash out of Treasury bills and private liquidity channels."
        falling = "Draining ON RRP balances releases liquid cash back into Treasury bills and broader risk assets."
    elif id_upper == "PPIFIS":
        overview = "Producer Price Index (PPI) Final Demand tracks average selling price changes received by domestic producers for goods and services."
        rising = "Upside cost pressure for manufacturers, which eventually passes through to consumer inflation (CPI) and compresses corporate margins."
        falling = "Wholesale disinflation, relieving margin pressures on businesses and presaging lower future CPI inflation prints."
    elif id_upper == "CPIAUCSL":
        overview = "The Consumer Price Index (CPI) tracks monthly price changes for a basket of goods and services purchased by urban households."
        rising = "Elevated inflation pressures central banks to raise interest rates, eroding real purchasing power and weighing on bond prices."
        falling = "Disinflation enables central bank rate cuts, lowering borrowing costs and expanding equity valuation multiples."
    elif id_upper == "CPILFESL":
        overview = "Core CPI excludes volatile food and energy prices to isolate underlying structural inflation trends."
        rising = "Persistent core inflation signals entrenched price pressures, forcing prolonged hawkish monetary policy."
        falling = "Core disinflation confirms underlying price stabilization, paving the way for monetary easing."
    elif id_upper == "PAYEMS":
        overview = "Total Nonfarm Payrolls measures net monthly job creation across all commercial and government sectors, excluding agricultural labor."
        rising = "Robust job creation fuels aggregate wage growth, consumer spending capacity, and broader GDP expansion."
        falling = "Slowing payroll growth or net job losses signal labor market weakness and potential recessionary contraction."
    elif id_upper == "UNRATE":
        overview = "The Unemployment Rate represents the percentage of the active labor force currently unemployed and actively seeking work."
        rising = "Elevated unemployment signals economic slack, reduced consumer spending capacity, and rising recession risks."
        falling = "Low unemployment indicates tight labor markets, supporting consumer income and economic growth."
    elif id_upper == "JTSJOL":
        overview = "JOLTS Job Openings tracks total unfulfilled job vacancies across nonfarm industries, measuring labor demand intensity."
        rising = "High openings relative to unemployed workers signal tight labor markets, worker shortages, and wage pressure."
        falling = "Declining openings indicate labor demand normalization, easing wage inflation without immediate mass layoffs."
    elif id_upper == "JTSQUR":
        overview = "The Quits Rate measures voluntary job departures as a percentage of total employment, reflecting worker confidence."
        rising = "High quits signal strong worker bargaining power, elevated job switching, and upward wage acceleration."
        falling = "Low quits signal worker caution, reduced job mobility, and cooling wage inflation."
    elif id_upper == "DGS10":
        overview = "The 10-Year Treasury Yield is the baseline risk-free discount rate for global capital markets."
        rising = "Higher 10Y yields elevate corporate borrowing costs, mortgage rates, and discount rates, compressing equity valuations."
        falling = "Lower 10Y yields ease long-term borrowing costs, support real estate activity, and expand stock valuation multiples."
    elif id_upper == "DGS2":
        overview = "The 2-Year Treasury Yield reflects short-term market expectations for Federal Reserve monetary policy over the coming 24 months."
        rising = "Rising 2Y yields price in hawkish Fed rate hikes or higher-for-longer policy expectations."
        falling = "Declining 2Y yields price in upcoming Fed rate cuts and monetary policy easing."
    elif id_upper == "T10Y2Y":
        overview = "The 10-Year minus 2-Year Treasury Yield Spread measures yield curve slope and term premium."
        rising = "Yield curve steepening during rate cut cycles historically signals impending macroeconomic adjustment or recession arrival."
        falling = "Yield curve inversion (2Y > 10Y) reflects market pricing of restrictive policy and tight money, historically preceding recessions by 12–18 months."
    elif id_upper == "VIXCLS":
        overview = "The CBOE Volatility Index (VIX) measures 30-day option-implied volatility for the S&P 500 index."
        rising = "Spiking VIX signals acute equity market fear, risk asset liquidations, and demand for portfolio hedging."
        falling = "Subdued VIX reflects market calm, low hedging demand, and stable bull market regime conditions."
    elif id_upper == "BAMLH0A0HYM2":
        overview = "The High Yield Option-Adjusted Spread measures the yield premium demanded for holding speculative-grade corporate bonds over Treasuries."
        rising = "Widening spreads signal heightened corporate default risk perceptions and tightening credit availability."
        falling = "Tightening spreads signal healthy corporate credit markets, low default fears, and robust risk appetite."
    elif id_upper == "M2SL":
        overview = "M2 Money Supply tracks liquid monetary assets including cash, checking deposits, savings accounts, and money market funds."
        rising = "Money supply expansion fuels nominal GDP growth, asset price liquidity, and potential long-term inflation."
        falling = "Money supply contraction drains broad economy liquidity, weighing on asset prices and nominal economic activity."
    elif id_upper == "WALCL":
        overview = "Federal Reserve Total Assets measure the size of the central bank’s balance sheet holdings."
        rising = "Balance sheet expansion (QE) injects liquidity into money markets and suppresses term premiums."
        falling = "Balance sheet runoff (QT) drains market liquidity and allows debt supply to be absorbed by private capital."

    return {
        "analysis_overview": overview,
        "impact_rising": rising,
        "impact_falling": falling,
    }


