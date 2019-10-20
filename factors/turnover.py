from core.adv_utlis import *
from core.portfolio import *
from core.allocate import *
import config

# Load Feature
turnover_path = r'/Users/oranbebai/Documents/Data/Finance/Extracted/DailyTurnover.csv'
turnover = pd.read_csv(turnover_path, index_col=0)

stock_nums = turnover.shape[1]  # Number of stocks, M
dates_nums = turnover.shape[0]  # Number of trade dates, N

# Load month tags
month_tags = config.month_tag

# Calculate daily average turnover of all stocks
average_turnover = turnover.mean(axis=1)

# Calculate average turnover of calender month
turnover_month = {}
for i in range(len(month_tags) - 1):
    turnover_month[month_tags[i+1]] = turnover[month_tags[i]: month_tags[i+1]].mean()
turnover_month = pd.DataFrame(turnover_month).T
turnover_monthly_path = os.path.join(config.feature_directory, 'M_Tover.csv')
turnover_month.to_csv(turnover_monthly_path)

# Daily turnover subtract daily average turnover
reduced_turnover = turnover.subtract(average_turnover, axis='index')

# For each trading day T, calculate the average turnover of T-125 to T-5
adjTover_daily = {}
for i in range(dates_nums):
    # Idiosyncratic turnover of each stock subtract mean of idiosyncratic turnover from T-125 to T-5
    if i < 125:
        continue
    date = reduced_turnover.index[i]
    adjTover_daily[date] = reduced_turnover.iloc[i] - reduced_turnover.iloc[i-125:i-5, :].mean()

# Adjusted daily turnover.DataFrame looks like (N-125) * M
average_of_120_days = pd.DataFrame(adjTover_daily).T
turnover_daily_path = os.path.join(config.feature_directory, 'D_AdjTover.csv')
average_of_120_days.to_csv(turnover_daily_path)

adjTove_monthly = {}
for i in range(len(month_tags) - 1):
    adjTove_monthly[month_tags[i+1]] = average_of_120_days[month_tags[i]: month_tags[i+1]].mean()
adjusted_monthly = pd.DataFrame(adjTove_monthly).T
adjTove_monthly_path = os.path.join(config.feature_directory, 'M_AdjTover.csv')
adjusted_monthly.to_csv(adjTove_monthly_path)

"""
Once the adjusted turnover is calculated, stocks can be allocated into different groups according to their features. 
2*3 groups and 5*5 groups are formed so that the adjTover factor can be calculated.
"""
# Load daily return and market value of all stocks
all_stocks_data_path = os.path.join(config.temp_data_path, 'AllStocksPortfolio.p')
all_stocks_data = Portfolio.load_pickle(all_stocks_data_path)

# Create Allocator Object
all_stocks_feature_path = os.path.join(config.temp_data_path, 'AllStocksAllocate.p')
all_stocks_feature = Allocate.load_pickle(all_stocks_feature_path)

# Add features.
all_stocks_feature.add_factor('adjTover', adjTove_monthly_path)
MV_monthly_path = os.path.join(config.feature_directory, 'M_MktV.csv')
all_stocks_feature.add_factor('MV', MV_monthly_path)

# allocate all A stocks into 2 * 3 groups to calculate turnover factor
Adj_MV_23_groups = all_stocks_feature.allocate_stocks_according_to_factors(['MV', 'adjTover'],
                                                                 [(0, 0.5, 1), (0, 0.3, 0.7, 1)])

Adj_MV_23_panel = generate_panel(all_stocks_data, config.period, Adj_MV_23_groups)
Adj_MV_23_panel.to_pickle('mv_adjTover_23')
Adj_MV_23_panel_ret = Adj_MV_23_panel.ret
turnover_factor = (Adj_MV_23_panel_ret.iloc[:, 0] - Adj_MV_23_panel_ret.iloc[:, 2] +
                   Adj_MV_23_panel_ret.iloc[:, 3] - Adj_MV_23_panel_ret.iloc[:, 5]) / 2

turnover_factor_path = os.path.join(config.factor_path, 'turnover.csv')
turnover_factor.to_csv(turnover_path)
print(1)
