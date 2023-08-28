import sqlite3
import typing as t
import pandas as pd
import datapane as dp 
import altair as alt
import seaborn as sns
import matplotlib.pyplot as plt

db = './sqlite/bright.db'
cm = sns.light_palette("green", as_cmap=True)

def run_query(q):
    with sqlite3.connect(db) as conn:
        return pd.read_sql(q,conn)
    
def run_command(c):
    with sqlite3.connect(db) as conn:
        conn.isolation_level = None
        conn.execute(c) 
        
def get_leads_approved():
    strQuery = '''
    SELECT b.value AS location
	    ,COUNT(lead_id) AS approved_leads
    FROM EVENT a INNER JOIN attribute B USING (lead_id)
    WHERE a.event_type = 'doc.subscriptionContract.approved'
	    AND b.name = 'region'
    GROUP BY b.value
    ORDER BY approved_leads DESC
    limit 10;
    '''
    return run_query(strQuery)

def get_lead_converted_approved():
    strQuery = '''
    SELECT sum(iif(a.event_type = 'doc.subscriptionContract.approved',1,0)) AS approved_leads
	,sum(iif(a.event_type = 'lead.created',1,0)) AS created_leads
    FROM EVENT A;
    '''
    return run_query(strQuery)

def get_lead_converted_visited():
    strQuery = '''
    SELECT sum(iif(a.event_type = 'doc.salesVisitReport.uploaded',1,0)) AS visited_leads
	,sum(iif(a.event_type = 'lead.created',1,0)) AS created_leads
    FROM EVENT A;
    '''
    return run_query(strQuery)


def create_fig(df,xdata,ydata):
    sns.reset_defaults
    sns.set_theme(style = "darkgrid", palette = "summer")
    plot = sns.barplot(data=df, x=xdata, y=ydata, palette = "summer")
    plot.set_xticklabels(plot.get_xticklabels(),rotation = 30)
    return plot

def create_hist(df1,xdata1,sub):
    fig, ax = plt.subplots()
    ax.hist(df1[xdata1], bins=15, label='Days to convert')
    plt.suptitle(sub)
    
    #sns.reset_defaults
    #sns.set_theme()
    #plot1 = sns.histplot(data = df1, x = xdata1, kde = True, bins="auto")   #.set(title='Number of days to convert')
    plot1=fig
    return plot1

def time_to_visit():
    strQuery = '''
    With visitedleads as (select lead_id,created_at as visit_date
                    from event
                    where event_type ='doc.salesVisitReport.uploaded')
    select distinct A.lead_id
	    ,max(A.created_at) as created
	    ,max(B.visit_date) as visited
	    ,round(julianday(max(B.visit_date)) -julianday(max(A.created_at)),0) as num_days
    from event A inner join visitedleads B using(lead_id)
    where a.event_type='lead.created'
    group by A.lead_id
    having num_days < 1791;
    '''
    return run_query(strQuery)

def time_to_connect():
    strQuery = '''
    with connectedleads as (select lead_id,created_at as connect_date
                    from event
                    where event_type ='doc.interconnection.approved')
    select distinct A.lead_id
	    ,max(A.created_at) as visited
	    ,max(B.connect_date) as connect
	    ,round(julianday(max(B.connect_date)) -julianday(max(A.created_at)),0) as num_days
    from event A inner join connectedleads B using(lead_id)
    where a.event_type='doc.subscriptionContract.approved'
    group by A.lead_id
    having num_days < 2262;
    '''
    return run_query(strQuery)

def isPositive(number):
    result=True
    if number < 0: 
        result = False
    return result

dfLeadsApproved = get_leads_approved()
dfLeadsConvertedApproved = get_lead_converted_approved()
dfLeadsConvertedVisited = get_lead_converted_visited()
dfTimeLeadsVisited = time_to_visit()
dfTimeLeadsConnect = time_to_connect()

cols = ','.join(dfLeadsApproved.columns)
view = dp.View(
    dp.Blocks(
    dp.Text(' BRIGHT. Leads Dashboard'),
    dp.Group(
        dp.BigNumber(
            heading='Leads approved vs created',
            value=str(round((dfLeadsConvertedApproved['approved_leads'][0]/dfLeadsConvertedApproved['created_leads'][0])*100,2)),
            change=str(abs(round(((dfLeadsConvertedApproved['approved_leads'][0]/dfLeadsConvertedApproved['created_leads'][0])*100)-5,2))),
            is_upward_change=isPositive(round(((dfLeadsConvertedApproved['approved_leads'][0]/dfLeadsConvertedApproved['created_leads'][0])*100)-5))
        ),
        dp.BigNumber(
            heading="Leads Visited vs created", 
            value=str(round((dfLeadsConvertedVisited['visited_leads'][0]/dfLeadsConvertedVisited['created_leads'][0])*100,2)),
            change=str(abs(round(((dfLeadsConvertedVisited['visited_leads'][0]/dfLeadsConvertedVisited['created_leads'][0])*100)-10,2))),
            is_upward_change=isPositive(round(((dfLeadsConvertedVisited['visited_leads'][0]/dfLeadsConvertedVisited['created_leads'][0])*100)-10,2))
        ),
        dp.BigNumber(
            heading = "Leads visited vs approved",
            value = str(round((dfLeadsConvertedApproved['approved_leads'][0]/dfLeadsConvertedVisited['visited_leads'][0])*100,2)),
            change = str(abs(round(((dfLeadsConvertedApproved['approved_leads'][0]/dfLeadsConvertedVisited['visited_leads'][0])*100)-50,2))),
            is_upward_change = isPositive(round(((dfLeadsConvertedApproved['approved_leads'][0]/dfLeadsConvertedVisited['visited_leads'][0])*100)-50,2)),
        ), columns=3
    ),
    dp.Text('Top 10 of locations with approved leads'),
    dp.Select(
        dp.Plot(create_fig(dfLeadsApproved,'location','approved_leads'), label="Chart"),
        dp.DataTable(dfLeadsApproved, label="Data")
    ),
    ),
    dp.Blocks(
        dp.Text('What time takes a lead to convert a visited lead?'),
        dp.Group(
            dp.BigNumber(
                heading = "Days to visit - Max",
                value = dfTimeLeadsVisited['num_days'].max(),
            ),
            dp.BigNumber(
                heading = "Days to visit - Min",
                value = dfTimeLeadsVisited['num_days'].min(),
            ),
            dp.BigNumber(
                heading = "Days to visit - Avg",
                value = round(dfTimeLeadsVisited['num_days'].mean()),
            ), columns=3
        ),
    dp.Select(
        dp.Plot(create_hist(dfTimeLeadsVisited,'num_days','Days to visit a lead'), label="Chart"),
        dp.DataTable(dfTimeLeadsVisited, label="Data"),
    ),
    ),
    dp.Blocks(
        dp.Text('What time takes an approved lead to be connected to CFE?'),
        dp.Group(
            dp.BigNumber(
                heading = "Days to connect - Max",
                value = dfTimeLeadsConnect['num_days'].max(),
            ),
            dp.BigNumber(
                heading = "Days to connect - Min",
                value = dfTimeLeadsConnect['num_days'].min(),
            ),
            dp.BigNumber(
                heading = "Days to connect - Avg",
                value = round(dfTimeLeadsConnect['num_days'].mean()),
            ), columns=3
        ),
        dp.Select(
        dp.Plot(create_hist(dfTimeLeadsConnect,'num_days','Days to connect a lead'), label="Chart"),
        dp.DataTable(dfTimeLeadsConnect, label="Data"),
    ),
    dp.Text('Dasboard generated with datapane library'),
    dp.Text('Horacio Morales González'),
    ),
)
#dp.save_report(view, path="layout_example.html")
#dp.serve_app(view, embed_mode=True)
dp.save_report(view, "bright.html", open=True)
