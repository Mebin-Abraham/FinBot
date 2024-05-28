from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import nltk
from nltk.stem import PorterStemmer
import re
import long_responses as long


nltk.download('punkt')

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

stemmer = PorterStemmer()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route("/chat")
@login_required
def index():
    return render_template('chat.html')

@app.route("/get", methods=["POST"])
@login_required
def chat():
    msg = request.form["msg"]
    user_input = msg
    return get_response(user_input)


def stem_words(words):
    return [stemmer.stem(word) for word in words]

def message_probability(user_message, recognised_words, single_response=False, required_words=[]):
    message_certainty = 0
    has_required_words = True

    stemmed_message = stem_words(user_message)
    stemmed_recognised_words = stem_words(recognised_words)
    stemmed_required_words = stem_words(required_words)

    for word in stemmed_message:
        if word in recognised_words:
            message_certainty += 1

    percentage = float(message_certainty) / float(len(recognised_words))

    for word in stemmed_required_words:
        if word not in stemmed_message:
            has_required_words = False
            break

    if has_required_words or single_response:
        return int(percentage * 100)
    else:
        return 0

def check_all_messages(message):
    highest_prob_list = {}

    def response(bot_response, list_of_words, single_response=False, required_words=[]):
        nonlocal highest_prob_list
        highest_prob_list[bot_response] = message_probability(message, list_of_words, single_response, required_words)

    response('Hello!', ['hello', 'hi', 'hey', 'sup', 'heyo'], single_response=True)
    response('See you!', ['bye', 'goodbye'], single_response=True)
    response('I\'m doing fine, and you?', ['how', 'are', 'you', 'doing'], required_words=['how'])
    response('You\'re welcome!', ['thank', 'thanks'], single_response=True)
    response('Thank you!', ['i', 'love', 'code', 'palace'], required_words=['code', 'palace'])
    response('I\'m a bot.', ['who', 'are', 'you'], required_words=['who'])
    response('1. Stocks<br>2. Mutual funds<br>3. FDs<br>4. RDs<br>5. Real estate<br>6. Gold',
             ['best', 'ways', 'to', 'invest'], required_words=['invest'])
    response('1. Axis Bank Ace Credit Card - Cashback<br>2. SBI Card Elite - Shopping, Travel & Movies<br>3. BPCL SBI Card Octane Credit Card - Fuel<br>4. Flipkart Axis Bank Credit Card - Online Shopping<br>5. Amazon Pay ICICI Credit Card - Online Shopping & Cashback<br>6. InterMiles HDFC Signature Credit Card - Travel<br>7. Axis Bank Vistara Signature Credit Card - Travel<br>8. HDFC Bank Diners Club Privilege Credit Card - Travel & Lifestyle',
        ['credit', 'card'], required_words=['credit', 'card'])
    response('Select the Category of Loans :<br>1. Personal Loan<br>2. Home Loan<br>3. Car Loan<br>4. Gold Loan',
             ['select', 'loans'], required_words=['loans'])
    response('1. HDFC (10.5%pa - 21.0%pa)<br>2. ICICI (10.75%pa - 19.0%pa)<br>3. Yes Bank (10.99%pa onwards - 20%pa)<br>4. Axis Bank (10.49%pa - 22%pa)<br>5. State Bank of India (11%pa - 14%pa)',
        ['Personal', 'loans', 'loan'], single_response=False, required_words=['Personal', 'loan'])
    response('1. Kotak Mahindra Bank: 8.75%pa onwards<br>2. Bank of Baroda: 9.15%pa onward<br>3. Bank of India: 8.45%pa onwards<br>4. State Bank of India: 9.15%pa onward',
        ['Home', 'loans', 'loan'], single_response=False, required_words=['Home', 'loan'])
    response('1. State Bank of India: 8.6%pa onwards<br>2. Canara Bank: 8.8%pa onwards<br>3. HDFC Bank: 9.3%pa onwards<br>4. ICICI Bank: 8.85%pa onwards',
        ['Car', 'loans', 'loan'], single_response=False, required_words=['Car', 'loan'])
    response('1. State Bank of India: 8.55%pa onwards<br>2. ICICI Bank: 9%pa onwards<br>3. Manappuram Finance: 12%pa onwards<br>4. Muthoot Finance: 12%pa onwards',
        ['Gold', 'loans', 'loan'], single_response=False, required_words=['Gold', 'loan'])
    response('The basic rule of thumb is to divide your monthly after-tax income into three spending categories: 50% for needs, 30% for wants and 20% for savings or paying off debt. By regularly keeping your expenses balanced across these main spending areas, you can put your money to work more efficiently.',
        ['save', 'money'], required_words=['money','save'])
    response('Start by tracking your expenses and income, then categorize and prioritize your spending. Set realistic goals, monitor your progress, and make adjustments as needed. Consider using budgeting apps or spreadsheets to help you stay organized.',
        ['set', 'budget', 'budgeting', 'stick'], required_words=['set','budget'])
    response('1. Take advantage of tax deductions when taking out a home loan.<br>2. Earn tax-exempt interest on savings accounts.<br>3. Receive tax-free interest on NRE accounts.<br>4. Maturity amount from life insurance policies can be tax-free.<br>5. Scholarships for education are exempt from income tax.',
        ['reduce', 'paying', 'taxes', 'tax'], required_words=['reduce','taxes'])
    response('Begin by educating yourself about the basics of stock market investing. Open a brokerage account, determine your investment strategy (such as long-term or short-term), and research potential investments. Consider diversifying your portfolio to mitigate risk.',
        ['invest', 'stock', 'stocks'], required_words=['stock', 'investing'])
    response('Pay bills on time, reduce credit card balances, keep credit utilization low, review credit reports for errors, maintain a long credit history, diversify credit mix, and avoid unnecessary account closures. Seek personalized advice for specific recommendations.',
        ['improve', 'credit', 'score', 'scores'], required_words=['score','score'])
    response('Begin by creating a repayment plan, prioritizing higher-interest debts first. Consider debt consolidation or refinancing options if it helps lower interest rates. Make consistent payments, avoid incurring new debts, and explore opportunities to increase your income.',
        ['debt', 'manage', 'loans'], required_words=['debt', 'manage'])
    response('Investing money in tax-saving instruments<br>Public Provident Fund<br>National Pension Scheme<br>Premium Paid for Life Insurance policy<br>National Savings Certificate',
        ['Income', 'tax'], required_words=['Income', 'save'])
    response('The decision to rent or buy depends on various factors, such as your financial stability, long-term plans, local housing market, and lifestyle preferences. Consider factors like affordability, stability, mobility, and personal goals before making a decision',
        ['rent', 'buy', 'home'], required_words=['rent'])
    response('As a salaried employee, before anything, you should understand your tax slab and meaning of your salary breakup components. This will help you figure out how to save on taxes. You need to understand what are the available deductions.<br>1. House Rent Allowance (HRA)<br>2. Leave Travel Allowance (LTA)<br>3. Employee Contribution to Provident Fund (PF)',
        ['taxes', 'income', 'salary', 'tax'], required_words=['salary','tax'])
    response('1. Not diversifying your portfolio enough.<br>2. Timing the market instead of focusing on long-term goals.<br>3. Ignoring risk management.<br>4. Overlooking fees and expenses.<br>5. Letting emotions drive investment decisions.',
        ['investment', 'mistakes'], single_response=False, required_words=['investment', 'mistakes'])
    response('1. Set clear retirement goals.<br>2. Contribute regularly to retirement accounts such as 401(k)s or IRAs.<br>3. Automate your savings.<br>4. Reduce unnecessary expenses.<br>5. Consider working with a financial advisor to create a retirement plan.',
        ['start', 'saving', 'retirement'], single_response=False, required_words=['start', 'saving', 'retirement'])
    response('1. Reduces risk by spreading investments across different asset classes.<br>2. Enhances potential for long-term returns.<br>3. Helps to hedge against market volatility.<br>4. Provides opportunities for growth in various market conditions.<br>5. Helps to maintain portfolio stability.',
        ['benefits', 'diversifying', 'investment'], single_response=False, required_words=['benefits', 'diversifying', 'investment'])
    response('1. Maintain a diversified portfolio.<br>2. Consider investing in defensive sectors.<br>3. Have a long-term investment horizon.<br>4. Stay informed and avoid panic selling.<br>5. Use options like stop-loss orders to limit losses.',
        ['protect', 'investments', 'market', 'downturns'], single_response=False, required_words=['protect', 'investments', 'market', 'downturns'])
    response('1. Create a budget and stick to it.<br>2. Prioritize high-interest debt.<br>3. Consider debt consolidation.<br>4. Negotiate lower interest rates.<br>5. Increase your income to pay off debt faster.',
        ['reducing', 'debt', 'strategies'], single_response=False, required_words=['reducing', 'reduce', 'debt', 'strategies'])
    response('1. Pay bills on time.<br>2. Keep credit card balances low.<br>3. Monitor your credit report regularly.<br>4. Avoid opening too many new accounts.<br>5. Maintain a mix of credit types.',
        ['improve', 'credit', 'score'], single_response=False, required_words=['improve', 'credit', 'score'])
    response('1. Risk of losing your home if you can’t repay the loan.<br>2. Possible reduction in home equity.<br>3. Higher interest rates compared to traditional mortgages.<br>4. Impact on your credit score if you default.<br>5. Fees and closing costs associated with the loan.',
        ['risks', 'borrowing', 'home equity'], single_response=False, required_words=['risks', 'borrowing', 'home equity'])
    response('1. Research current interest rates.<br>2. Improve your credit score.<br>3. Shop around and compare offers.<br>4. Highlight your creditworthiness to lenders.<br>5. Consider refinancing or consolidating existing loans.',
        ['negotiate', 'lower', 'interest rate'], single_response=False, required_words=['negotiate', 'lower', 'interest rate'])
    response('1. Take advantage of business expenses such as office supplies and equipment.<br>2. Deduct qualified business meals and entertainment expenses.<br>3. Contribute to retirement accounts like SEP IRAs or Solo 401(k)s.<br>4. Claim the home office deduction if applicable.<br>5. Work with a tax professional to identify all available deductions.',
        ['maximize', 'tax deductions', 'small business owner'], single_response=False, required_words=['maximize', 'tax deductions', 'small business owner'])
    response('1. Tax treatment: Contributions to traditional IRAs may be tax-deductible, while Roth IRA contributions are made with after-tax dollars.<br>2. Withdrawals: Traditional IRA withdrawals are generally taxed as ordinary income, while qualified Roth IRA withdrawals are tax-free.<br>3. Age restrictions: Traditional IRAs have required minimum distributions (RMDs) starting at age 72, while Roth IRAs do not have RMDs during the owner’s lifetime.',
        ['differences', 'traditional', 'Roth', 'IRAs'], single_response=False,required_words=['differences', 'traditional', 'Roth', 'IRAs'])
    response('As a salaried employee, before anything, you should understand your tax slab and the meaning of your salary breakup components. This will help you figure out how to save on taxes. You need to understand what are the available deductions.',
        ['tax', 'reduction', 'employee'], single_response=False, required_words=['tax', 'reduction', 'employee']),
    response('Research various loan options and compare interest rates and terms. Consider factors such as repayment flexibility, prepayment penalties, and customer service reputation when choosing a lender.',
        ['loan', 'research', 'interest', 'rate'], single_response=False, required_words=['loan', 'research', 'interest', 'rate']),
    response('Prioritize higher-interest debts first when creating a repayment plan. Explore debt consolidation or refinancing options to lower interest rates. Make consistent payments and avoid incurring new debts.',
        ['loan', 'repayment', 'consolidation'], single_response=False, required_words=['loan', 'repayment', 'consolidation']),
    response('Understand the risks associated with borrowing, including the possibility of losing your home if you can’t repay the loan, reduction in home equity, higher interest rates compared to traditional mortgages, impact on your credit score if you default, and fees and closing costs associated with the loan.',
        ['loan', 'risks', 'borrowing'], single_response=False, required_words=['loan', 'risks', 'borrowing']),
    response('Choose credit cards that align with your spending habits and financial goals. Consider factors such as annual fees, rewards programs, interest rates, and customer service quality when selecting a credit card.',
        ['credit', 'card', 'choose'], single_response=False, required_words=['credit', 'card', 'choose']),
    response('Use credit cards responsibly by paying bills on time, keeping credit card balances low, monitoring your credit report regularly, avoiding opening too many new accounts, and maintaining a mix of credit types.',
        ['credit', 'card', 'responsibly'], single_response=False, required_words=['credit', 'card', 'responsibly']),
    response("If you're considering a credit card, compare various options available in the market. Look for benefits such as cashback, rewards points, low interest rates, and additional perks like travel insurance or airport lounge access.",
        ['credit', 'card', 'compare'], single_response=False, required_words=['credit', 'card', 'compare'])
    response('As an Indian citizen, you can utilize various tax-saving options to reduce your tax liability. Some effective tax-saving hacks include:<br>1. Invest in tax-saving instruments like Public Provident Fund (PPF), National Pension Scheme (NPS), Equity Linked Saving Schemes (ELSS), and Sukanya Samriddhi Yojana (SSY).<br>2. Utilize deductions under Section 80C for investments in Employee Provident Fund (EPF), Life Insurance Premiums, and Equity Linked Saving Schemes (ELSS).<br>3. Maximize deductions under Section 80D for health insurance premiums for self, family, and parents.<br>4. Take advantage of deductions under Section 80TTA for interest earned on savings accounts.<br>5. Utilize deductions under Section 80G for donations made to eligible charities and institutions.',
        ['tax', 'saving', 'tips', 'India'], single_response=False,required_words= ['tax', 'saving', 'tips', 'India']),
    response('In India, there are various loan options available to meet different financial needs:<br>1. Personal Loan: Used for various purposes such as wedding expenses, medical emergencies, or travel.<br>2. Home Loan: To purchase or construct a house or apartment.<br>3. Car Loan: To purchase a new or used car.<br>4. Education Loan: For higher education expenses, both in India and abroad.<br>5. Business Loan: For starting or expanding a business venture.<br>Ensure to compare interest rates, processing fees, and repayment terms before choosing a loan option.',
        ['loan', 'options', 'India'], single_response=False, required_words=['loan', 'options', 'India']),
    response('Effective budgeting is crucial for managing finances efficiently. Here are some budgeting tips for Indian citizens:<br>1. Track your expenses using apps like Walnut, Money Manager, or YNAB (You Need a Budget).<br>2. Categorize expenses into fixed (rent, utilities) and variable (dining out, entertainment).<br>3. Prioritize essential expenses like groceries, rent, and utility bills.<br>4. Allocate a portion of your income for savings and investments.<br>5. Review your budget regularly and make adjustments as needed to meet financial goals.',
        ['budgeting', 'tips', 'India'], single_response=False, required_words=['budgeting', 'tips', 'India']),
    response('Mutual funds are popular investment options in India, offering diversification and professional management. Consider investing in mutual funds based on your investment goals, risk tolerance, and investment horizon. Some popular mutual fund categories in India include:<br>1. Equity Funds: Invest primarily in stocks, suitable for long-term wealth creation.<br>2. Debt Funds: Invest in fixed-income securities like bonds and government securities, providing stable returns with lower risk.<br>3. Hybrid Funds: Invest in a mix of equity and debt instruments, offering a balance of risk and returns.<br>4. Index Funds: Track benchmark indices like Nifty or Sensex, providing returns similar to the underlying index.<br>5. Tax-Saving Funds (ELSS): Offer tax benefits under Section 80C of the Income Tax Act, with a lock-in period of three years.',
        ['mutual', 'funds', 'India'], single_response=False, required_words=['mutual', 'funds', 'India']),
    response('Gold is considered a traditional investment option in India, offering stability and hedging against inflation. Indian citizens can invest in gold through various avenues:<br>1. Physical Gold: Purchase gold jewelry, coins, or bars from jewelers or banks.<br>2. Gold ETFs (Exchange-Traded Funds): Invest in gold electronically through stock exchanges like NSE or BSE.<br>3. Gold Sovereign Bonds: Invest in government-backed gold bonds issued by RBI, offering interest and capital appreciation.<br>4. Gold Mutual Funds: Invest in mutual funds that invest in gold-related assets, providing diversification and professional management.<br>5. Gold Savings Schemes: Participate in gold savings schemes offered by jewelers or banks, allowing systematic investment in gold over time.',
        ['gold', 'investment', 'India'], single_response=False, required_words=['gold', 'investment', 'India']),
    response('Real estate is a popular investment avenue in India, offering potential for capital appreciation and rental income. Indian citizens can invest in real estate through various options:<br>1. Residential Properties: Purchase apartments, villas, or plots for personal use or rental income.<br>2. Commercial Properties: Invest in office spaces, retail outlets, or warehouses for rental income and capital appreciation.<br>3. REITs (Real Estate Investment Trusts): Invest in REITs listed on stock exchanges, providing exposure to real estate assets and regular dividends.<br>4. Real Estate Crowdfunding: Participate in real estate projects through online crowdfunding platforms, pooling funds with other investors.<br>5. Real Estate Funds: Invest in real estate funds managed by asset management companies, offering professional management and diversification across properties.',
        ['real', 'estate', 'India'], single_response=False, required_words=['real', 'estate', 'India']),
    response('Retirement planning is essential for Indian citizens to ensure financial security during their golden years. Here are some retirement planning tips:<br>1. Start Early: Begin investing for retirement as early as possible to benefit from the power of compounding.<br>2. Utilize Provident Funds: Contribute to EPF (Employee Provident Fund) and PPF (Public Provident Fund) for tax benefits and retirement savings.<br>3. Invest in NPS: Open an NPS (National Pension System) account for long-term retirement savings with flexibility and tax benefits.<br>4. Consider Annuity Plans: Purchase annuity plans from insurance companies to receive regular income post-retirement.<br>5. Review and Adjust: Regularly review your retirement plan, adjusting contributions and investments based on changing financial goals and market conditions.',
        ['retirement', 'planning', 'India'], single_response=False, required_words=['retirement', 'planning', 'India']),
    response('Maximize your tax savings with these smart strategies:<br>1. Utilize Section 80C Deductions: Invest in tax-saving instruments like PPF, ELSS, NSC, and EPF to claim deductions up to ₹1.5 lakh.<br>2. Opt for NPS Contributions: Contribute to NPS (National Pension System) and claim an additional deduction of up to ₹50,000 under Section 80CCD(1B).<br>3. Claim HRA Exemption: If you\'re a salaried individual, claim HRA (House Rent Allowance) exemption based on your rent payments, HRA received, and place of residence.<br>4. Utilize Home Loan Benefits: Avail deductions on home loan repayments under Sections 24(b) and 80C for interest and principal repayments, respectively.<br>5. Invest in Health Insurance: Purchase health insurance for yourself, your family, and your parents to claim deductions under Section 80D.<br>6. Opt for LTA Exemption: Utilize Leave Travel Allowance (LTA) for domestic travel expenses and claim exemptions under Section 10(5).<br>7. Consider Education Loan Interest: Claim deductions on interest paid for education loans under Section 80E for yourself, spouse, or children\'s higher education.<br>8. Invest in Tax-Free Bonds: Consider investing in tax-free bonds issued by government entities like NHAI or REC for tax-free interest income.<br>9. Maximize EPF Contributions: Increase your EPF (Employee Provident Fund) contributions to maximize tax savings and retirement corpus.<br>10. Consult a Tax Advisor: Seek professional advice from a tax consultant or financial planner to optimize your tax-saving strategies and ensure compliance with tax laws.',
        ['tax', 'saving', 'hacks', 'India'], single_response=False, required_words=['tax', 'saving', 'India']),
    response('Here are more strategies to maximize your tax savings in India:<br>11. Utilize Section 80DDB: Claim deductions for medical treatment of specified diseases for yourself or dependents under Section 80DDB.<br>12. Invest in Sukanya Samriddhi Yojana: Secure your daughter\'s future by investing in the Sukanya Samriddhi Yojana and avail deductions under Section 80C.<br>13. Deduct Professional Tax: Deduct professional tax paid during the financial year from your taxable income.<br>14. Use Section 80G: Contribute to approved charitable institutions and claim deductions under Section 80G for the donated amount.<br>15. Opt for Section 80TTA: Earn interest income from savings accounts and claim deductions up to ₹10,000 under Section 80TTA.<br>16. Invest in RGESS: Benefit from tax deductions under the Rajiv Gandhi Equity Savings Scheme (RGESS) for first-time equity investors.<br>17. Claim LTA for Family: Utilize LTA exemptions for family members, including spouse, children, and dependent parents, on travel expenses.<br>18. Explore Section 80U: If you have a disability, claim deductions under Section 80U for yourself or a dependent family member.<br>19. Consider Section 10(14): Enjoy tax-free perks like food coupons, medical reimbursement, and transport allowance provided by your employer.<br>20. Utilize Section 80GGA: Claim deductions for donations made to scientific research or rural development under Section 80GGA of the Income Tax Act.',
        ['tax', 'saving', 'hacks', 'India', 'additional'], single_response=False, required_words=['tax', 'saving', 'hacks', 'India'])

    # Longer responses
    response(long.R_ADVICE, ['give', 'advice'], required_words=['advice'])
    response(long.R_EATING, ['what', 'you', 'eat'], required_words=['you', 'eat'])

    best_match = max(highest_prob_list, key=highest_prob_list.get)
    return long.unknown() if highest_prob_list[best_match] < 1 else best_match

def get_response(user_input):
    split_message = re.split(r'\s+|[,;?!.-]\s*', user_input.lower())
    response = check_all_messages(split_message)
    return response

if __name__ == "__main__":
    app.run()
# Testing the response system
while True:
    print('Bot: ' + get_response(input('You: ')))