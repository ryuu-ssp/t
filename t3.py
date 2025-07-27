
import streamlit as st 
import pandas as pd
import matplotlib.pyplot as plt


st.set_page_config(
    page_title="Cashflow management",
    layout="wide"
)


st.title('Cashflow management')
df = pd.read_excel("20250624_ตัวอย่าง.xlsx", sheet_name="Sheet5")

st.write(df)


st.title('AR & AP DAYS')




# คำนวณค่าเฉลี่ย
dfarday     = int(df.loc[df['ประเภท']=='ลูกหนี้','ระยะเวลา'].mean().round())
dfarontime  = int(df.loc[df['ประเภท']=='ลูกหนี้','diff'].mean().round())
dfapday     = int(df.loc[df['ประเภท']=='เจ้าหนี้','ระยะเวลา'].mean().round())
dfapontime  = int(df.loc[df['ประเภท']=='เจ้าหนี้','diff'].mean().round())

# แสดงผลแบบ Metric
col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="AR DAYS",
        value=f"{dfarday} วัน",
        delta=f"{dfarontime:+d} วัน(ช้า/เร็ว)",
        delta_color="inverse"   # บวก=แดง, ลบ=เขียว
    )

with col2:
    st.metric(
        label="AP DAYS",
        value=f"{dfapday} วัน",
        delta=f"{dfapontime:+d} วัน(ช้า/เร็ว)",
        delta_color="normal"    # default: บวก=เขียว, ลบ=แดง
        # หรือจะไม่ใส่ delta_color ก็ได้ เพราะ default คือ normal
    )




dfar = df[df['ประเภท'] == 'ลูกหนี้']


# 1) เฉลี่ยระยะเวลา
avg_duration = (
    dfar
    .groupby('ชื่อ')['ระยะเวลา']
    .mean()
    .sort_values(ascending=False)
    .rename('avg_duration')
    .to_frame()
)

# 2) ยอดเงินรวม
total_amount = (
    dfar
    .groupby('ชื่อ')['จำนวนเงิน']
    .sum()
    .sort_values(ascending=False)
    .rename('total_amount')
    .to_frame()
)

late_counts = (
    dfar[dfar['diff'] > 0]
    .groupby('ชื่อ')['diff']
    .count()
    .rename('late_freq')
)

# นับรายการทั้งหมดต่อชื่อ
total_counts = (
    dfar
    .groupby('ชื่อ')['diff']
    .count()
    .rename('total_count')
)

# คำนวณ % การจ่ายเกิน
late_pct = (
    pd.concat([late_counts, total_counts], axis=1)
    .assign(late_pct=lambda x: (x['late_freq'] / x['total_count']) * 100)
    .sort_values('late_pct', ascending=False)
    [['late_pct']]  # แสดงเฉพาะคอลัมน์ late_pct
)

# เปลี่ยนชื่อคอลัมน์ให้ดูดี
late_pct.columns = ['% จ่ายเกินเวลา']
late_pct = late_pct.round(0)






st.title('วิเคราะห์พฤติกรรมลูกหนี้')

# สร้างสามคอลัมน์เรียงจากซ้ายไปขวา
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("เฉลี่ยระยะเวลา")
    st.write(avg_duration)

with col2:
    st.subheader("ยอดเงินรวม")
    st.write(total_amount)

with col3:
    st.subheader("% จ่ายเกินเวลา")
    st.write(late_pct)






df_grouped = df.groupby(['วันที่จะได้รับ/จ่าย', 'ประเภท'])['จำนวนเงิน'].sum().unstack(fill_value=0).reset_index()
start_date = df_grouped['วันที่จะได้รับ/จ่าย'].min()
end_date = df_grouped['วันที่จะได้รับ/จ่าย'].max()
date_range = pd.date_range(start=start_date, end=end_date, freq='D')
df_dates = pd.DataFrame({'วันที่': date_range})
df_grouped.rename(columns={'วันที่จะได้รับ/จ่าย': 'วันที่'}, inplace=True)


# 3. รวมกับ df_dates (ซึ่งมีทุกวันในช่วง มิ.ย. - ธ.ค. 2025)
df_merged = df_dates.merge(df_grouped, on='วันที่', how='left')

# 4. เติมค่า NaN ที่เกิดจากไม่มีธุรกรรมวันนั้น ด้วย 0
df_merged['ลูกหนี้'] = df_merged['ลูกหนี้'].fillna(0)
df_merged['เจ้าหนี้'] = df_merged['เจ้าหนี้'].fillna(0)

# 5. คำนวณกระแสเงินสดสุทธิ
df_merged['net cash'] = df_merged['ลูกหนี้'] + df_merged['เจ้าหนี้']  # เจ้าหนี้เป็นค่าลบอยู่แล้ว

cash_accum  = st.number_input(
    'กรุณาใส่ค่าเงินสดยกมา:',
    value=0.0,
    step=10000.0,
    format="%.0f"
)


df_merged['เงินสดสะสม'] = df_merged['net cash'].cumsum() + cash_accum



df_merged['วันที่'] = pd.to_datetime(df_merged['วันที่'])

# ตั้ง 'วันที่' เป็น index
df_merged = df_merged.set_index('วันที่')



st.title('เงินสดสะสมรายวัน')

# คราวนี้ st.line_chart จะใช้ index (วันที่) เป็นแกน x ให้อัตโนมัติ
st.line_chart(df_merged['เงินสดสะสม'])
df_merged[:]





dfap = df[df['ประเภท'] == 'เจ้าหนี้']

# 1) ระยะเวลาเฉลี่ย 10 รายการที่ระยะเวลาสั้นที่สุด
avg_durationap = (
    dfap
    .groupby('ชื่อ')['ระยะเวลาที่กำหนด']
    .mean()
    .sort_values(ascending=True)
    .head(10)
    .rename('ระยะเวลาเฉลี่ย (น้อยสุด 10 อันดับ)')
    .to_frame()
)

# 2) ยอดเงินรวม 10 รายการที่จำนวนเงินน้อยที่สุด
total_amountap = (
    dfap
    .groupby('ชื่อ')['จำนวนเงิน']
    .sum()
    .sort_values(ascending=True)
    .head(10)
    .rename('ยอดเงินรวม (น้อยสุด 10 อันดับ)')
    .to_frame()
)

st.title('วิเคราะห์พฤติกรรมเจ้าหนี้')

# สร้างสองคอลัมน์เรียงจากซ้ายไปขวา
col1, col2 = st.columns(2)

with col1:
    st.subheader("ระยะเวลาเฉลี่ย 10 อันดับที่่น้อยสุด")
    st.table(avg_durationap)

with col2:
    st.subheader("ยอดเงินรวม 10 อันดับที่มากสุด")
    st.table(total_amountap)


























st.title('วางแผนการจ่าย')







threshold = st.number_input(
    'กรุณาใส่ค่า threshold (จำนวนเงินขั้นต่ำ):',
    min_value=0.0,
    value=13000000.0,
    step=10000.0,
    format="%.0f"
)


# 1) เตรียม DataFrame รายการเจ้าหนี้แบบละเอียด
df_ap = df[df['ประเภท']=='เจ้าหนี้'][['วันที่จะได้รับ/จ่าย','ชื่อ','จำนวนเงิน']].copy()
df_ap.columns = ['วันที่','ชื่อเจ้าหนี้','จำนวนเงิน']
df_ap['วันที่'] = pd.to_datetime(df_ap['วันที่'])

# 2) merge กับ df_merged เพื่อเอาค่าเงินสดสะสม ณ วันนั้นมาใช้
df_ap = df_ap.merge(
    df_merged[['เงินสดสะสม']], 
    left_on='วันที่', 
    right_index=True,
    how='left'
).sort_values('วันที่')

# 3) loop แต่ละรายการเจ้าหนี้ เพื่อดูว่าถ้าเงินสดต่ำกว่า threshold ให้เลื่อนไปวันถัดไปที่พอจ่ายได้
payment_plan = []
for _, row in df_ap.iterrows():
    orig_date = row['วันที่']
    creditor  = row['ชื่อเจ้าหนี้']
    amount    = row['จำนวนเงิน']
    cash      = row['เงินสดสะสม']
    
    if cash < threshold:
        # หา index ของ orig_date ใน df_merged
        pos = df_merged.index.get_loc(orig_date)
        j = pos + 1
        while j < len(df_merged) and df_merged.iloc[j]['เงินสดสะสม'] < threshold:
            j += 1
        if j < len(df_merged):
            new_date = df_merged.index[j]
            payment_plan.append({
                'ชื่อเจ้าหนี้': creditor,
                'วันที่เดิม':       orig_date,
                'วันที่จ่ายใหม่':  new_date,
                'จำนวนเงินที่เลื่อน': amount
            })

# 4) สร้าง DataFrame สรุป
df_payment_plan = pd.DataFrame(payment_plan)

# แสดงตารางใน Streamlit
st.subheader('สรุปแผนเลื่อนชำระ')
st.write(df_payment_plan)






df_adjusted = df_merged.copy()

# 2) ปรับ net cash: ลบรายการเจ้าหนี้ออกจากวันที่เดิม และเพิ่มเข้าไปที่วันที่จ่ายใหม่
for _, row in df_payment_plan.iterrows():
    orig = row['วันที่เดิม']
    new  = row['วันที่จ่ายใหม่']
    amt  = row['จำนวนเงินที่เลื่อน']
    # ลบที่เดิม (AP = ลบ)
    df_adjusted.loc[orig, 'net cash'] -= amt  # เพราะใน df_merged เจ้าหนี้เป็นค่าลบอยู่แล้ว
    # เพิ่มที่ใหม่
    df_adjusted.loc[new, 'net cash']  += amt

# 3) คำนวณเงินสดสะสมใหม่
df_adjusted['เงินสดสะสม_adjusted'] = df_adjusted['net cash'].cumsum() + cash_accum

# 4) วาดกราฟเปรียบเทียบ
st.subheader('เปรียบเทียบเงินสดสะสม ก่อน–หลังเลื่อนชำระ')
# รวม Series สองตัวเข้า DataFrame เดียว
df_compare = pd.DataFrame({
    'ก่อนเลื่อน':   df_merged['เงินสดสะสม'],
    'หลังเลื่อน': df_adjusted['เงินสดสะสม_adjusted']
})
# ใช้ st.line_chart สร้างกราฟ
st.line_chart(df_compare)
