import streamlit as st
import openai
import PyPDF2
import re
import json

# ====================================
# Inject Custom CSS for UI Enhancements
# ====================================
def inject_css():
    custom_css = """
    <style>
        /* Global styling */
        body {
            background-color: #f9fafb;
            color: #2c3e50;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        }
        .main .block-container {
            max-width: 900px;
            padding: 2rem;
            margin: auto;
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        }
        h1, h2, h3 {
            color: #1f4e79;
        }
        /* Card styling */
        .card {
            background-color: #ffffff;
            border: 1px solid #e5e5e5;
            border-radius: 6px;
            padding: 16px;
            margin: 8px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: transform 0.2s ease-in-out;
        }
        .card:hover {
            transform: scale(1.02);
        }
        .card-header {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #1f4e79;
        }
        .card-content {
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
        }
        /* Summary Card for qualification status */
        .summary-card {
            background-color: #eef9f1;
            border: 2px solid;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
        }
        /* Button styling */
        .cta-button {
            background-color: #2c7a7b;
            color: #ffffff;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        .cta-button:hover {
            background-color: #285e61;
        }
        /* Expander Header */
        .streamlit-expanderHeader {
            font-size: 16px;
            font-weight: 600;
            color: #1f4e79;
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

# ====================================
# Currency Conversion Function
# ====================================
def convert_currency_to_usd(text: str) -> str:
    """
    Convert monetary values in UGX, KES, TZS, and RWF to USD.
    
    Conversion factors:
      - 1 USD = 3700 UGX
      - 1 USD = 115 KES
      - 1 USD = 2400 TZS
      - 1 USD = 1080 RWF
    """
    conversion_rates = {
        "UGX": 3700,
        "KES": 115,
        "TZS": 2400,
        "RWF": 1080
    }
    
    pattern = re.compile(r"(\d[\d,\.]*)\s*(UGX|KES|TZS|RWF)")
    
    def replacer(match):
        amount_str = match.group(1).replace(',', '')
        currency = match.group(2)
        try:
            amount_val = float(amount_str)
        except ValueError:
            return match.group(0)
        usd_value = amount_val / conversion_rates[currency]
        return f"${usd_value:,.2f} USD"
    
    return pattern.sub(replacer, text)

# ====================================
# Eligibility Criteria (truncated version)
# ====================================
CRITERIA = r"""
2. What loans qualify for support?
Qualifying loans are loans that meet the following eligibility criteria:
1. Tenor between 90 days and 7 years. Aceli Africa does not support loans of less than 90 days or more than 7 (seven) years for Origination Incentives and 5 (five) years for First Loss Cover. For credit lines and other revolving facilities, the tenor is the term of the facility itself – not the timespan during which a Borrower draws on it.
2. Market range. Aceli Africa seeks to catalyze a commercial financial market over time and awards incentives for loans within a generally accepted market range. We do not impose any minimum or maximum interest rate bands, but we will be monitoring interest rate setting for market distortion and abusive rate setting.
3. Loan value between $15K* or $25K and $1.75M. Aceli Africa seeks to catalyze a financial market for agricultural SMEs and does not support microloans or loans to larger enterprises. We recognize that exchange rate fluctuations and other factors can affect the dollar value of loans submitted for incentives and will consider loan amounts that reasonably overshoot or undershoot the maximum or minimum loan value.
To be considered for the first-loss cover, the Approved Principal Amount of the loans must fall within the following ranges (or the equivalent amount in the applicable Local Currency):

First Loss Cover
Loan Range
Formal value chains
Informal value chains
Range*
Countries
Range*
Countries
New Borrowers
$25,000 -$1.25M
All
$25,000 - $1.75M
All
Returning Borrowers
$25,000 - $1M
Kenya & Rwanda
$25,000 - $1.5M
Kenya & Rwanda
$50,000 - $1M
Uganda & Tanzania
$50,000 - $1.5M
Uganda & Tanzania
Repeat borrowers (previously new)
$25,000 - $1M
All
$25,000 - $1.5M
All
Repeat borrowers
(previously returning)
$25,000 - $1M
Kenya & Rwanda
$25,000 - $1.5M
Kenya & Rwanda
$50,000 - $1M
Uganda & Tanzania
$50,000 - $1.5M
Uganda & Tanzania
8
*Minimum loan value for special categories as of August 2023: The minimum loan ticket size drops to $15,000 for the following borrower segments as of mid-2023: businesses that are majority owned by women or by youth age 35 and under, businesses that meet Aceli's Climate & Environment impact criteria, as well as businesses that do not meet the C&E criteria but are accessing loans specifically to acquire climate technologies. This applies for new, returning, and repeat borrowers, as well as for all value chains and all countries. Loans to borrower segments that do not meet the above criteria will continue to have a minimum ticket size of $25,000.

4. Agricultural purpose. With the exception of tobacco, Aceli Africa supports agricultural loans that finance agricultural inputs, primary production, aggregation and trade, post-harvest handling, and processing. Aceli also accepts loans issued to a qualifying borrower to support or enhance the performance of their agricultural activity. For example, loans to purchase an irrigation pump or system for their crops, loans for cold storage to reduce post-harvest losses or extend the shelf life of agricultural produce, etc. For clarity, the agricultural value chain that the borrower is primarily involved in will apply. However, qualifying loans MUST NOT be made in connection with the restructuring, full refinancing, full repayment or full repurchase of existing debt. Only qualifying loans with a portion of up to 30% for refinancing or repurchase of existing debt – provided that the un-refinanced portion of 70% is within the Aceli loan ticket range – will be considered eligible.
5. Loan Type: Letters of credit, credit cards, wholesale loans, performance bonds or guarantees, and overdraft facilities are not eligible for Aceli incentives;
6. Aceli Registration: A qualifying loan must be registered with Aceli no later than 90 days from the earliest between the effective date and signing date of the loan agreement.
7. Qualified borrower. The loan must have been issued to a qualified Borrower as set out below.

3. What borrowers qualify for support?
Qualified Borrowers are Borrowers that are approved by Aceli in its sole discretion and shall without limitation meet the following eligibility criteria:
1. Annual revenues. The Borrower should have reported average annual revenues greater than $50K* and less than $10M in the most recently available records of a full financial year to qualify for the first-loss cover. The Borrower should have reported annual revenues greater than $30k and less than $3M for the origination incentives. For startups in their first year of operations where no annual revenue figures are available, Aceli will consider the promoter's contribution to the project being financed in lieu of annual revenues. The promoter's contribution shall range between $30,000 - $3million for OI eligibility, and between $30,000 - $10 million for FLC eligibility.
*Annual revenue requirements for special categories as of August 2023: The minimum annual revenue drops to $30,000 for the following borrower segments as of mid-2023: businesses that are majority owned by women or by youth age 35 and under, businesses that meet Aceli's Climate & Environment impact criteria, as well as businesses that do not meet the C&E criteria but are accessing loans specifically to acquire climate technologies. This applies for new, returning, and repeat borrowers, as well as for all value chains and all countries. Loans to other borrower segments are required to have a minimum of $50,000 in annual revenue as has been the case since Aceli Africa's inception.
2. Conflict of interest. The Borrower should not be an equity owner, director, partner, or affiliate of the Lender. Moreover, the Lender should not have any direct or indirect interest (as determined by Aceli) in the Borrower.
3. Registration. The Borrower must be registered under the laws of an African jurisdiction. However, Aceli may approve Borrowers registered in Mauritius, Europe, or the US at its sole discretion.
4. Default. The Borrower must not have defaulted on any loans that qualified for Aceli support.
5. Minimum social impact. The Borrower must provide at least one of the following services:
   (a) created market access for at least 25 smallholder farmers, (b) sold farm inputs or other services for at least 100 smallholder farmers, or (c) generated employment for at least 5 full time employees. Further information on minimum social impact can be found in the ESG policy.
6. Excluded activities. Finally, the loan must not be advanced to a Borrower involved in any excluded activities (see Annex I for a non-exhaustive list of exclusions).

4. What is Aceli's first-loss cover?
Aceli Africa's first-loss cover addresses systemic market risks to increase Lender risk appetite. Our benchmarking data shows that lending to the agriculture sector entails higher systemic risk than other sectors, especially when loans are made to first-time Borrowers and early stage enterprises. Our first-loss cover is designed to cover the incremental risk that Lenders incur when they serve these high-risk market segments. Lending to high-risk segments generates first-loss reserves at a portfolio level. Traditional loan guarantees cover losses at the loan-level. Aceli Africa's first-loss product is accrued at the loan-level but covers losses at the portfolio-level (hence "portfolio"). In practice this means: the first-loss cover is automatically allocated to the lender's reserve account as soon as Aceli Africa has established that the loan meets the qualification criteria. If the loan does default, the lender may draw down on the reserve. If the loan does not default, the lender may use the accrued first-loss cover for one loan to cover losses incurred on other loans in the portfolio. Finally, Aceli Africa allows the lender to draw on its reserves to cover loan loss before exhausting recovery options (thus "first-loss").

a) When are my loans eligible?
Combining risk mitigation products. We understand that Lenders often have different risk mitigation products at their disposal and might choose to optimize risk coverage by applying two or more products to the same loan. Aceli allows participating Lenders to combine its first-loss cover with other third-party credit support. However, the support must be reported and the sum of Aceli first-loss cover and other third-party credit support should not be greater than 70% of the Qualified Loan. For instance, a typical loan guarantee program covers 50% of a Lender's losses on that loan. If the loan were $200k, the Lender would in principle be eligible to accrue Aceli first-loss reserves on $200k and could draw on the reserves commensurate with that amount. If the guarantee covers 70% or more of the loan, the Lender would not be eligible to accrue first-loss reserves for that loan.
Restructuring. Lenders must inform Aceli Africa of any Qualified Loans that are restructured after they have been registered with Aceli.
Recovery proceeds. When an acceleration event occurs to any Qualified Loan, Lenders can draw on their reserves before exhausting recovery options as long as they can sufficiently demonstrate, in Aceli's sole opinion, proof that they applied reasonable recovery efforts. Any amount that is subsequently recovered from a Qualified Loan which has gone into default must be credited into the reserve account and used for portfolio first-loss protection (in the case of Regulated Qualified Lenders) or reimbursed to Aceli (in the case of Unregulated Qualified Lenders).
Common borrower. Two or more accredited Lenders can lend to the same Borrower within a calendar year and accrue first-loss reserves based on its respective loan size, provided that the loan amount for each falls within the qualifying range.
Multiple Loans per calendar year. Each Qualified Borrower may borrow more than one Qualified Loan; provided that:
   i. the Approved Principal Amount of all outstanding Qualified Loans to a single Qualified Borrower shall not exceed $2 million in the aggregate at any time;
   ii. all such Qualified Loans must have distinct purposes and uses (e.g., one for working capital and one for capital expenditures);
   iii. Typically, only one Qualified Loan for each distinct purpose and use may be made by the same Lender to the same Qualified Borrower during a single 12-month period or a single agricultural cycle.
   iv. In any case, Aceli shall limit to two the number of qualified loans by the same lender to the same borrower for the same purpose in a single 12-month period if a) the loans are for a different growing season of the same crop; or b) for different crops. The minimum tenor for such loans shall be six (6) months.
Syndicated loan. In the case of a syndicated loan, the total loan amount must be within the allowable range to be considered for the first-loss cover. The syndicate lead arranger will register the full loan with Aceli and take the responsibility for distributing the First Loss Cover payout among the group of lenders.
Loan registration period. Based on current donor commitments, Lenders will be able to register loans with Aceli through to year-end 2024. Incentives for any loans registered that remain outstanding at year-end 2024 will be honored.

b) How is the coverage calculated?
Accrual rates. Lenders will accrue first-loss reserves at pre-established rates outlined in the curves above. Our data shows that systemic risk is higher for new borrowers and informal value chains ("higher risk factors") and lower for returning borrowers and formal value chains ("lower-risk factors"). Loans that qualify for both higher risk factors will accrue the highest percentage of first-loss reserves: 6% of loan value. Loans that qualify for one of the higher risk factors and one of the lower risk factors will accrue less: 4%. Loans that are associated with both lower risk factors will accrue the least: 2%. At loan values above $1M for informal value chains and $750k for formal value chains, the accrual rates phase out until 0%. In informal value chains, the accrual rate phases out completely at $1.75M for new borrowers and $1.5M for returning borrowers. In formal value chains, the accrual rate phases out completely at $1.25M and $1M for new and returning borrowers, respectively. The higher first-loss cover for loans that meet impact criteria is discussed in part 6 of these guidelines.
Outstanding principal. The first-loss cover will be applied upon partial or full disbursement of the Qualified Loan and will be calculated using the lesser of (1) the peak average month-end balance of the Qualified Loan for two consecutive calendar months and (2) the original maximum principal amount of loan.
Adjustments. Aceli will, at its sole discretion, adjust the first-loss cover rates. Any such adjustments will be communicated to Lenders and will not be applied to Qualified Loans that have previously been registered with Aceli.

c) What is the process of earning first-loss cover?
1. Lender sources new or returning Borrowers.
2. Lender performs due diligence and ensures that the information that Aceli Africa requires to evaluate baseline social impact and higher impact is logged in the process.
3. Lender makes a Qualified Loan.
4. Lender submits monthly, quarterly and annual reports regarding the number and amount of Qualified Loans it originated and their financial performance.
5. Aceli confirms that the loan qualifies and credits the Lender's first-loss reserve or virtual account in US dollars.
6. Lender submits a first-loss claim with supporting documentation upon the occurrence of an acceleration event.

d) Examples

e) What is the process of making a first-loss claim?
1. Lender submits a first-loss claim with supporting documentation upon the occurrence of an acceleration event. Submission should take place no earlier than 30 days after an acceleration (loss) event and no later than 120 days after such event.
2. Lender will be required to demonstrate that such a loss event has occurred. Such documentation may include: (i) copies of demand letters sent to the borrower and (ii) minutes of investment/credit committee confirming the write-off decision.
3. The request must be submitted by an authorized signatory of the Qualified Lender. The list of authorized signatories for the Qualified Lender shall be included in the Legal Agreement.
4. Aceli shall use commercially reasonable efforts to validate and respond to any claim requests within 15 days of receipt of all required documentation in support of such request.

5. What is Aceli's origination incentive?
Origination incentives defray higher operating costs of lending to early-stage SMEs that are unprofitable to serve in the short term. Origination incentives increase revenue for Lenders where loan underwriting and management costs are higher than what high-impact borrowers can afford.
Loans below $500k are eligible for origination incentives. Our benchmarking data confirms that the operating costs of loans under this size on average become too high to be offset by interest and fees affordable to agricultural SMEs.
Origination incentives are paid directly into the accounts of Lenders and are immediately considered earned. However, payment is only affected once a loan has been outstanding for 90 days. In contrast, first-loss cover is credited into the lender's reserve account and can only be drawn upon the occurrence of an acceleration event.

a) How are origination incentives calculated?
Amounts. Lenders are awarded origination incentives at the pre-established dollar amounts calculated by the table below and visualized in the curve below. Like the first-loss cover, a distinction is made between new and returning Borrowers; unlike the first-loss cover, no distinction is made between value chains. The higher origination incentives for loans that meet impact criteria is discussed in part 6 of these guidelines.

Loan value         New borrower         Returning borrower         Repeat Borrower
$25,000* to $99,999    10% of principal     6% of principal         6% of principal
$100,000 to $199,999   $10,000            $6,000                 $6,000
$200,000 to $500,000   Amounts for loans in the [$100,000 to $199,999] range are phased out evenly on a straight-line basis

*Minimum loan value for special categories as of August 2023: The minimum loan ticket size drops to $15,000 for the following borrower segments as of mid-2023: businesses that are majority owned by women or by youth age 35 and under, businesses that meet Aceli's Climate & Environment impact criteria, as well as businesses that do not meet the C&E criteria but are accessing loans specifically to acquire climate technologies. This applies for new, returning, and repeat borrowers, as well as for all value chains and all countries. Loans to borrower segments that do not meet the above criteria will continue to have a minimum ticket size of $25,000.

Common borrower. Two or more accredited Lenders can lend to the same Borrower within a calendar year and both Lenders will be awarded an origination incentive as long as the loan amount of each loan falls within the qualifying range.
Multiple loans per calendar year. Each Qualified Borrower may borrow more than one Qualified Loan; provided that:
   i. the Approved Principal Amount of all outstanding Qualified Loans to a single Qualified Borrower shall not exceed $2 million in the aggregate at any time;
   ii. all such Qualified Loans must have distinct purposes and uses (e.g., one for working capital and one for capital expenditures);
   iii. Typically, only one Qualified Loan for each distinct purpose and use may be made by the same Lender to the same Qualified Borrower during a single 12-month period or a single agricultural cycle.
   iv. In any case, Aceli shall limit to two the number of qualified loans by the same lender to the same borrower for the same purpose in a single 12-month period if a) the loans are for a different growing season of the same crop; or b) for different crops. The minimum tenor for such loans shall be six (6) months.
Syndicated loan. In the case of a syndicated loan, only the Lender who originates/arranges the Qualified Loan will be entitled to receive an origination incentive, provided that their portion of the loan falls within the qualifying range. The total amount of the syndicated loan should also fall within the qualifying range.
Currency. Origination incentives are denominated in USD dollars and will be paid to Lenders in the same currency.

b) What is the process?
1. Lender sources new or returning borrowers.
2. Lender performs due diligence.
3. Lender makes a qualifying loan.
4. Lender submits monthly, quarterly and annual reports regarding the number and amount of qualifying loans it originated and their financial performance, along with supporting documentation.
5. If Aceli confirms that the loan qualifies and has been outstanding for 90 days, Aceli makes a direct payment in US dollars to an account that the Lender elects.
6. Lender may allocate the incentive payment as lending revenue.

6. What is the impact bonus?
Aceli Africa will award additional first-loss cover and origination incentives for Qualified Loans that meet a higher impact standard. The eligible impact areas are Food security and nutrition, Gender inclusion, Climate and Environment and Youth Inclusion.
a) When are my loans eligible?
   - Food security and nutrition. Aceli incentivizes loans that contribute to the increased production or improved nutrition of food crops for consumption in Africa. To earn this impact bonus, the loan must be to a Borrower that meets one of several criteria defined in Aceli's ESG policy.
   - Gender inclusion. Aceli Africa incentivizes loans that contribute to gender inclusion of women as owners, business leaders or managers, employees, suppliers, and/or consumers. Aceli has adopted the criteria for gender-inclusive investment defined by the 2X Challenge. Loans will earn an additional impact bonus for gender inclusion if they meet at least one of several criteria defined in Aceli's ESG policy.
   - Climate and environment. Aceli will award an impact bonus for loans to Borrowers that promote regenerative agriculture and circular agri-based systems. Loans that have received certification from Rainforest Alliance/UTZ, Organic and forest stewardship will also be considered for the climate smart impact bonus. Concretely, the enterprise must promote or align with the practices defined by Aceli's ESG policy.
   - Youth inclusion. Aceli Africa incentivizes loans that contribute to youth inclusion through ownership, business leaders or managers, employees and suppliers are eligible for impact bonus.
The impact areas have been tiered into sub-impact areas and qualified loans will receive additional bonus if they meet the impact areas for both sub-impact areas as outlined below:
   - Gender:
       o Gender – Leadership
       o Gender – Partnership
   - Food security and Nutrition:
       o Food security
       o Nutrition
   - Climate and Environment:
       o Climate and Environment – Regenerative
       o Climate and Environment – Circular
       o Climate Tech2
   - Youth Inclusion:
       o Youth Inclusion
       o Youth-owned businesses
The Impact Bonus is calculated based on the level of contributions that loans make to the four impact and sub-impact areas. Refer to Aceli ESG policy for more details.
Special origination bonus as of August 2023: To incentivize lending to SMEs that are majority-owned by women or by youth 35 and under, SMEs with strong climate and environment practices, and SMEs that are accessing loans specifically to acquire climate technologies, Aceli has introduced an additional origination bonus for loans that meet any of these three impact areas. Lenders will receive an additional $1K in Origination Incentives for loans that meet any of the criteria mentioned above. Details are further below in the table for the Origination Incentives.
"""
# ====================================
# PDF Text Extraction Function
# ====================================
def extract_text_from_pdf(pdf_file):
    """
    Extract text from an uploaded PDF file using PyPDF2.
    """
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF file: {e}")
        return None

# ====================================
# OpenAI Analysis Function
# ====================================
def get_recommendation(pdf_text, criteria_text, openai_api_key):
    """
    Use OpenAI's ChatCompletion API to analyze the loan document.
    """
    openai.api_key = openai_api_key

    prompt = f"""
You are an expert loan eligibility analyst. You are thorough, detailed and precise. You ensure that every loan is 100% reviewed for compliance with the eligibility criteria. Analyze the following loan document data extract against the eligibility criteria for Aceli support. The eligibility criteria must always be met 100% in full - no exceptions.
Provide a concise final recommendation with key metrics and a detailed explanation. Any local currencies mentioned must also have their USD currency equivalent. End your response with either "Qualifies" or "Does Not Qualify"
--- Loan Document Extract ---
{pdf_text}

--- Eligibility Criteria for Aceli Support ---
{criteria_text}
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a precise loan eligibility review analyst. You always ensure loans are 100% compliant with the eligibility criteria."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.8,
        )
        recommendation = response.choices[0].message['content'].strip()
        return recommendation
    except Exception as e:
        st.error(f"Error from OpenAI API: {e}")
        return None

# ====================================
# Improved UI: Display Analysis & Recommendation Results in a Tabular Format
# ====================================
def show_analysis(analysis_text):
    """
    Display the analysis results in a modern, visually distinct format
    """
    try:
        # Parse the analysis text
        if isinstance(analysis_text, str):
            try:
                data = json.loads(analysis_text)
            except json.JSONDecodeError:
                data = {
                    "qualifies": "Qualifies" in analysis_text,
                    "explanation": analysis_text
                }
        else:
            data = analysis_text

        # Extract qualification status
        qualifies = data.get("qualifies", False)
        
        # Create dashboard layout
        st.markdown("""
        <style>
        .dashboard-container { margin: 2em 0; }
        .status-badge {
            padding: 1em 2em;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 2em;
            animation: fadeIn 0.5s ease-in;
        }
        .status-badge h2 {
            color: white !important;
            margin: 0;
        }
        .metric-container {
            background: white;
            padding: 1.5em;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 1em;
        }
        .metric-title {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 0.5em;
        }
        .metric-value {
            font-size: 1.2em;
            font-weight: bold;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        </style>
        """, unsafe_allow_html=True)

        # Status Badge
        status_color = "#28a745" if qualifies else "#dc3545"
        status_text = "QUALIFIES. PROCEED WITH THE REVIEW PROCESS" if qualifies else "DOES NOT QUALIFY. CONSULT YOUR LENDER"
        st.markdown(f"""
            <div class="status-badge" style="background-color: {status_color};">
                <h2>{status_text}</h2>
            </div>
        """, unsafe_allow_html=True)

        # Create single tab for detailed analysis
        tab1 = st.tabs(["Detailed Analysis"])[0]

        with tab1:
            # Create expandable sections for detailed analysis
            if "explanation" in data:
                with st.expander("Full Analysis", expanded=True):
                    st.write(data["explanation"])
            
            # Visual progress indicators
            st.markdown("### Compliance Score")
            progress = 100 if qualifies else 60  # Example score
            st.progress(progress/100)
            st.markdown(f"**{progress}%** compliant with requirements")

    except Exception as e:
        st.error(f"Error displaying analysis: {str(e)}")

# ====================================
# Main Application Code
# ====================================
def main():
    inject_css()
    
    st.title("Aceli loan eligibility checker ✅")
    st.markdown("""
    This application uses OpenAI's GPT4o model to review whether a loan qualifies for Aceli support.
    """)
    
    # Request OpenAI API key from the user
    openai_api_key = st.text_input("Enter your OpenAI API Key:", type="password")
    if not openai_api_key:
        st.info("Please enter your OpenAI API key to proceed.")
        return

    # PDF file uploader
    pdf_file = st.file_uploader("Upload a PDF file containing the loan information", type=["pdf"])
    if pdf_file is not None:
        pdf_text = extract_text_from_pdf(pdf_file)
        if pdf_text:
            # Convert local currency amounts to USD
            converted_text = convert_currency_to_usd(pdf_text)
            st.success("PDF text extracted and currency conversion applied!")
            with st.expander("Show Extracted & Converted PDF Text"):
                st.write(converted_text)
            
            # Button to trigger analysis
            if st.button("Analyze Loan Document"):
                with st.spinner("Analyzing the document..."):
                    recommendation = get_recommendation(converted_text, CRITERIA, openai_api_key)
                if recommendation:
                    show_analysis(recommendation)
                else:
                    st.error("No recommendation received. Please try again.")
        else:
            st.error("Failed to extract text from the PDF. Please check the file and try again.")

if __name__ == '__main__':
    main()
