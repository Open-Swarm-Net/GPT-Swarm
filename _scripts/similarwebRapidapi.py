import csv
import requests
import json

# read URLs from CSV file
with open('./_files/websites.csv', newline='') as csvfile:
    urls = [row['URLs'] for row in csv.DictReader(csvfile)]

# define output CSV file
output_file = './_files/output.csv'

# define headers for the output CSV file
headers = ['Site', 'Visits', 'YearMonthData', 'TopCountriesCodes', 'TopCountries%', 'Month-2', 'Month-3', 'Category', 'TrafficSources', 'BounceRate']

# write headers to output CSV file
with open(output_file, mode='w', newline='') as outfile:
    writer = csv.writer(outfile)
    writer.writerow(headers)

# loop through URLs and get data from SimilarWeb API
for url in urls:
    api_url = 'https://similar-web.p.rapidapi.com/get-analysis'
    api_key = ''
    headers = {'X-RapidAPI-Key': api_key, 'X-RapidAPI-Host': 'similar-web.p.rapidapi.com'}
    params = {'domain': url}
    response = requests.get(api_url, headers=headers, params=params)

    # parse response JSON
    data = response.json()
    visits = data['Engagments']['Visits']
    year_month_data = sorted(data['EstimatedMonthlyVisits'].keys())[-1]
    top_countries = sorted(data['TopCountryShares'], key=lambda x: x['Value'], reverse=True)
    top_countries_codes = ' / '.join([c['CountryCode'] for c in top_countries])
    top_countries_percentages = ' / '.join([str(round(c['Value'] * 100, 1)) + '%' for c in top_countries])
    month_2 = data['EstimatedMonthlyVisits'][sorted(data['EstimatedMonthlyVisits'].keys())[-2]]
    month_3 = data['EstimatedMonthlyVisits'][sorted(data['EstimatedMonthlyVisits'].keys())[-3]]
    category = data['Category']
    traffic_sources = sorted(data['TrafficSources'].items(), key=lambda x: x[1] or 0, reverse=True)
    traffic_sources_names = ' / '.join([t[0] for t in traffic_sources])
    bounce_rate = data['Engagments']['BounceRate']

    # write data to output CSV file
    with open(output_file, mode='a', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow([url, visits, year_month_data, top_countries_codes, top_countries_percentages, month_2, month_3, category, traffic_sources_names, bounce_rate])
