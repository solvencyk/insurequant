import json,sys
p=sys.argv[1]
d=json.load(open(p,encoding='utf-8'))
print(d.get('status'),len(d.get('list',[])))
for a in d['list']:
    if a.get('account_id')=='ifrs-full_IncomeTaxExpenseContinuingOperations' or a.get('account_id')=='ifrs-full_ProfitLossBeforeTax':
        print({k:v for k,v in a.items() if k in('sj_div','account_id','account_nm','thstrm_amount','thstrm_add_amount','frmtrm_amount','frmtrm_add_amount','frmtrm_q_amount','bfefrmtrm_amount')})
