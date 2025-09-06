
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Table, MetaData
import folium
from streamlit_folium import st_folium

# ------------------------
# إعداد قاعدة البيانات SQLite
# ------------------------
engine = create_engine('sqlite:///users.db', echo=False)
metadata = MetaData()

users_table = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('username', String, unique=True),
    Column('password', String)
)

favorites_table = Table('favorites', metadata,
    Column('id', Integer, primary_key=True),
    Column('username', String),
    Column('item_type', String),
    Column('item_name', String)
)

metadata.create_all(engine)
conn = engine.connect()

# ------------------------
# بيانات وهمية للعقارات والبيوت مع صور واقعية
# ------------------------
lands_data = pd.DataFrame([
    {"name": "أرض 1", "area": 250, "price": 30000, "location": "مدينة الكويت",
     "image": "https://cdn.pixabay.com/photo/2017/01/31/13/14/house-2022467_1280.png", "lat": 29.3759, "lon": 47.9774},
    {"name": "أرض 2", "area": 400, "price": 50000, "location": "الجابرية",
     "image": "https://cdn.pixabay.com/photo/2016/03/31/19/58/house-1293990_1280.jpg", "lat": 29.3375, "lon": 48.0183},
    {"name": "أرض 3", "area": 600, "price": 75000, "location": "الفروانية",
     "image": "https://cdn.pixabay.com/photo/2017/05/10/19/42/architecture-2304375_1280.jpg", "lat": 29.3370, "lon": 47.9900},
])

houses_data = pd.DataFrame([
    {"name": "بيت جاهز 1", "area": 200, "price": 60000, "location": "مدينة الكويت",
     "image": "https://cdn.pixabay.com/photo/2017/01/31/13/14/house-2022467_1280.png", "lat": 29.3759, "lon": 47.9774},
    {"name": "بيت جاهز 2", "area": 350, "price": 120000, "location": "الجابرية",
     "image": "https://cdn.pixabay.com/photo/2016/03/31/19/58/house-1293990_1280.jpg", "lat": 29.3375, "lon": 48.0183},
    {"name": "بيت جاهز 3", "area": 500, "price": 200000, "location": "الفروانية",
     "image": "https://cdn.pixabay.com/photo/2017/05/10/19/42/architecture-2304375_1280.jpg", "lat": 29.3370, "lon": 47.9900},
])

# ------------------------
# دالة تقدير تكلفة البناء
# ------------------------
def estimate_building_cost(area, rooms, material_type):
    base_price = 200
    material_multiplier = {"عادي": 1, "فاخر": 1.5, "فخم": 2}
    return int(area * base_price * material_multiplier.get(material_type, 1) + rooms*1000)

# ------------------------
# واجهة تسجيل الدخول / إنشاء حساب
# ------------------------
def login_page():
    st.markdown("<h1 style='text-align: center; color: #2F4F4F;'>مرحبا بك في موقع العقارات بالكويت</h1>", unsafe_allow_html=True)
    choice = st.radio("تسجيل دخول أو إنشاء حساب", ["تسجيل دخول", "إنشاء حساب"], horizontal=True)

    if choice == "إنشاء حساب":
        st.subheader("إنشاء حساب جديد")
        new_user = st.text_input("اسم المستخدم")
        new_pass = st.text_input("كلمة المرور", type="password")
        if st.button("إنشاء حساب"):
            result = conn.execute(users_table.select().where(users_table.c.username==new_user)).fetchone()
            if result:
                st.warning("اسم المستخدم موجود مسبقًا!")
            else:
                conn.execute(users_table.insert().values(username=new_user, password=new_pass))
                st.success("تم إنشاء الحساب! يمكنك الآن تسجيل الدخول.")
    else:
        st.subheader("تسجيل الدخول")
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        if st.button("تسجيل دخول"):
            result = conn.execute(users_table.select().where(users_table.c.username==username)).fetchone()
            if result and result['password'] == password:
                st.success(f"مرحبا {username}!")
                st.session_state['login'] = True
                st.session_state['username'] = username
            else:
                st.error("اسم المستخدم أو كلمة المرور خاطئة!")

# ------------------------
# حفظ المفضلات
# ------------------------
def add_to_favorites(username, item_type, item_name):
    conn.execute(favorites_table.insert().values(username=username, item_type=item_type, item_name=item_name))
    st.success("تم إضافة العقار إلى المفضلات!")

def show_favorites(username):
    st.subheader("مفضلاتك")
    favs = conn.execute(favorites_table.select().where(favorites_table.c.username==username)).fetchall()
    if favs:
        for f in favs:
            st.write(f"{f['item_type']}: {f['item_name']}")
    else:
        st.info("لا توجد مفضلات بعد.")

# ------------------------
# الصفحة الرئيسية بعد تسجيل الدخول
# ------------------------
def main_page():
    st.markdown("<h1 style='text-align: center; color: #2F4F4F;'>موقع شراء وتصميم البيوت والأراضي بالكويت</h1>", unsafe_allow_html=True)
    st.write(f"مرحبًا، **{st.session_state['username']}**!")
    option = st.selectbox("اختر القسم", ["شراء أرض", "تصميم بيت", "شراء بيت جاهز", "مفضلاتك"])

    # ---------- شراء أرض ----------
    if option == "شراء أرض":
        st.subheader("شراء أرض")
        area = st.selectbox("المساحة المطلوبة (م²)", [200, 250, 300, 400, 500, 600])
        budget = st.selectbox("الميزانية المتوقعة", [30000, 50000, 75000, 100000, 150000])
        location = st.selectbox("المنطقة", ["مدينة الكويت", "الجابرية", "الفروانية"])
        if st.button("بحث"):
            results = lands_data[(lands_data["area"]>=area) & 
                                 (lands_data["price"]<=budget) & 
                                 (lands_data["location"]==location)]
            if not results.empty:
                for i, row in results.iterrows():
                    st.markdown(f"<div style='border:1px solid #ccc; border-radius:10px; padding:10px; margin:5px; background-color:#F0F8FF'>", unsafe_allow_html=True)
                    st.image(row["image"], width=300)
                    st.write(f"**{row['name']}** | المساحة: {row['area']} | السعر: {row['price']} | الموقع: {row['location']}")
                    if st.button(f"أضف {row['name']} للمفضلات", key=f"land_{i}"):
                        add_to_favorites(st.session_state['username'], "أرض", row['name'])
                    st.markdown("</div>", unsafe_allow_html=True)
                # الخريطة
                m = folium.Map(location=[29.3759, 47.9774], zoom_start=11)
                for i, row in results.iterrows():
                    folium.Marker([row['lat'], row['lon']], popup=row['name']).add_to(m)
                st_folium(m, width=700, height=400)
            else:
                st.info("لا توجد أراضٍ مطابقة للمعايير.")

    # ---------- تصميم بيت ----------
    elif option == "تصميم بيت":
        st.subheader("تصميم بيت")
        area = st.selectbox("مساحة البيت (م²)", [50, 100, 150, 200, 250, 300])
        rooms = st.selectbox("عدد الغرف", [1,2,3,4,5])
        floors = st.selectbox("عدد الطوابق", [1,2,3])
        material_type = st.selectbox("نوع المواد", ["عادي", "فاخر", "فخم"])
        if st.button("عرض تصميم 3D للبيت"):
            cost = estimate_building_cost(area, rooms, material_type)
            st.success(f"تقدير تكلفة البناء: {cost} دينار كويتي")
            if material_type == "عادي":
                img_url = "https://cdn.pixabay.com/photo/2017/01/31/13/14/house-2022467_1280.png"
            elif material_type == "فاخر":
                img_url = "https://cdn.pixabay.com/photo/2016/03/31/19/58/house-1293990_1280.jpg"
            else:
                img_url = "https://cdn.pixabay.com/photo/2017/05/10/19/42/architecture-2304375_1280.jpg"
            st.image(img_url, width=400)
            st.info(f"عدد الطوابق: {floors}, عدد الغرف: {rooms}, المواد: {material_type}")

    # ---------- شراء بيت جاهز ----------
    elif option == "شراء بيت جاهز":
        st.subheader("شراء بيت جاهز")
        area = st.selectbox("المساحة المطلوبة (م²)", [200, 300, 350, 400, 500])
        budget = st.selectbox("الميزانية المتوقعة", [60000, 120000, 150000, 200000])
        location = st.selectbox("المنطقة", ["مدينة الكويت", "الجابرية", "الفروانية"])
        if st.button("بحث"):
            results = houses_data[(houses_data["area"]>=area) & 
                                  (houses_data["price"]<=budget) & 
                                  (houses_data["location"]==location)]
            if not results.empty:
                for i, row in results.iterrows():
                    st.markdown(f"<div style='border:1px solid #ccc; border-radius:10px; padding:10px; margin:5px; background-color:#F5F5DC'>", unsafe_allow_html=True)
                    st.image(row["image"], width=300)
                    st.write(f"**{row['name']}** | المساحة: {row['area']} | السعر: {row['price']} | الموقع: {row['location']}")
                    if st.button(f"أضف {row['name']} للمفضلات", key=f"house_{i}"):
                        add_to_favorites(st.session_state['username'], "بيت جاهز", row['name'])
                    st.markdown("</div>", unsafe_allow_html=True)
                # الخريطة
                m = folium.Map(location=[29.3759, 47.9774], zoom_start=11)
                for i, row in results.iterrows():
                    folium.Marker([row['lat'], row['lon']], popup=row['name']).add_to(m)
                st_folium(m, width=700, height=400)
            else:
                st.info("لا توجد بيوت جاهزة مطابقة للمعايير.")

    # ---------- مفضلات المستخدم ----------
    else:
        show_favorites(st.session_state['username'])

# ------------------------
# تشغيل التطبيق
# ------------------------
if 'login' not in st.session_state:
    st.session_state['login'] = False

if not st.session_state['login']:
    login_page()
else:
    main_page()
