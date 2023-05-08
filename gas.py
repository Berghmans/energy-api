from entsog import EntsogPandasClient
import pandas as pd

client = EntsogPandasClient()

start = pd.Timestamp('20230404', tz='Europe/Brussels')
end = pd.Timestamp('20230405', tz='Europe/Brussels')
country_code = 'BE'

points = client.query_operator_point_directions()
points.to_excel("test.xlsx")
mask = points['point_label'].str.contains('ZTP')
masked_points = points[mask]
print(masked_points["point_label"].unique())

keys = []
for idx, item in masked_points.iterrows():
    keys.append(f"{item['operator_key']}{item['point_key']}{item['direction_key']}")
print(keys)
# keys = ["BE-TSO-0001LNG-00017entry", "BE-TSO-0001LNG-00017exit"]

# data = client.query_operational_point_data(start = start, end = end, indicators = ['physical_flow'], point_directions = keys, verbose = False)

# print(data.head())
# client.query_connection_points()
# print(client.query_operators()["operator_label"].to_string())
# client.query_balancing_zones()
# client.query_operator_point_directions(country_code)
# client.query_interconnections()
# client.query_aggregate_interconnections()
# client.query_urgent_market_messages()
# client.query_tariffs(start = start, end = end, country_code = country_code)
# client.query_tariffs_sim(start = start, end = end, country_code = country_code)

# operational_options = {
#     interruption_capacity : "Actual interruption of interruptible capacity",
#     allocation : "Allocation",
#     firm_available : "Firm Available",
#     firm_booked : "Firm Booked",
#     firm_interruption_planned : "Firm Interruption Planned - Interrupted",
#     firm_interruption_unplanned :"Firm Interruption Unplanned - Interrupted",
#     firm_technical : "Firm Technical",
#     gcv : "GCV",
#     interruptible_available : "Interruptible Available",
#     interruptible_booked : "Interruptible Booked",
#     interruptible_interruption_actual : "Interruptible Interruption Actual – Interrupted",
#     interruptible_interruption_planned : "Interruptible Interruption Planned - Interrupted",
#     interruptible_total : "Interruptible Total",
#     nomination : "Nomination",
#     physical_flow : "Physical Flow",
#     firm_interruption_capacity_planned : "Planned interruption of firm capacity",
#     renomination : "Renomination",
#     firm_interruption_capacity_unplanned : "Unplanned interruption of firm capacity",
#     wobbe_index : "Wobbe Index",
#     oversubscription_available : "Available through Oversubscription",
#     surrender_available : "Available through Surrender",
#     uioli_available_lt : "Available through UIOLI long-term",
#     uioli_available_st : "Available through UIOLI short-term"
# }

# with Path("tariffsfulls.json").open(mode="r", encoding="utf-8") as file_handle:
#     data = json.load(file_handle)

# filtered = {
#     tariff["operatorPointDirection"]
#     for tariff in data["tariffsfulls"]
# }

# print(filtered)
