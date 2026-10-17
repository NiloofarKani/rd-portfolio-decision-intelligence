import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Synthetic, illustrative inputs: no patient, company, or market data.
# Scores 0-100 are independent expert-assessment placeholders, not validated measures.
projects = [
 ('ONC-101','Oncology','Phase III',95,78,82,76,110,360,0.64),
 ('IMM-202','Immunology','Phase II',68,86,74,88,75,205,0.42),
 ('RAR-303','Rare Disease','Phase II',96,28,63,74,50,95,0.51),
 ('ONC-104','Oncology','Phase I',72,92,90,58,40,180,0.19),
 ('NEU-105','Neurology','Preclinical',90,62,54,70,30,120,0.11),
 ('CAR-306','Cardiovascular','Phase III',60,90,78,67,85,240,0.68),
 ('INF-207','Infectious Disease','Phase II',87,44,58,50,45,85,0.38),
 ('MET-208','Metabolic','Phase II',55,96,87,92,80,300,0.41),
 ('RAR-109','Rare Disease','Phase I',94,18,45,82,25,55,0.20),
 ('HEM-310','Hematology','Phase III',83,66,72,85,70,175,0.62),
]
fields = ['project_id','therapeutic_area','stage','medical_need_score','market_demand_score',
          'strategic_fit_score','competitive_position_score','next_stage_funding_usd_m',
          'illustrative_peak_sales_usd_m','illustrative_probability_of_approval']
with (ROOT/'portfolio_projects.csv').open('w',newline='',encoding='utf-8') as f:
    writer=csv.writer(f); writer.writerow(fields); writer.writerows(projects)

# Screening classifications are discussion aids, not investment recommendations.
def screen(p):
    _,_,_,need,demand,fit,_,_,_,_ = p
    if need>=70 and demand>=60: return 'High need / High demand'
    if need>=70: return 'High need / Low demand'
    if demand>=60: return 'Low need / High demand'
    return 'Low need / Low demand'

with (ROOT/'screening_matrix.csv').open('w',newline='',encoding='utf-8') as f:
    writer=csv.writer(f); writer.writerow(['project_id','screening_quadrant'])
    writer.writerows((p[0],screen(p)) for p in projects)

print(f'Created {len(projects)} synthetic projects')
print('Total next-stage funding request: $'+str(sum(p[7] for p in projects))+'M')
for q in ['High need / High demand','High need / Low demand','Low need / High demand','Low need / Low demand']:
    print(q+': '+', '.join(p[0] for p in projects if screen(p)==q))
