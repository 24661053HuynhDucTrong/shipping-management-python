import pyodbc
import pandas as pd
import matplotlib.pyplot as plt
import gradio as gr
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import io

# ========================
# KẾT NỐI SQL SERVER
# ========================
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost,1433;DATABASE=Northwind;"
    "UID=sa;PWD=Vietnam@123;TrustServerCertificate=yes"
)

def get_connection():
    return pyodbc.connect(conn_str)

# ========================
# TAB 1: QUẢN LÝ ĐƠN HÀNG
# ========================
def show_orders():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT o.OrderID, o.OrderDate, o.ShippedDate,
               o.ShipCountry, s.CompanyName AS Shipper
        FROM Orders o
        JOIN Shippers s ON o.ShipVia = s.ShipperID
        WHERE o.ShippedDate IS NOT NULL
        ORDER BY o.OrderID DESC
    """, conn)
    conn.close()
    df['OrderDate'] = pd.to_datetime(df['OrderDate']).dt.date
    df['ShippedDate'] = pd.to_datetime(df['ShippedDate']).dt.date
    return df

# ========================
# TAB 2: THỐNG KÊ BIỂU ĐỒ
# ========================
def show_chart():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT s.CompanyName AS Shipper, COUNT(*) AS TotalOrders
        FROM Orders o
        JOIN Shippers s ON o.ShipVia = s.ShipperID
        WHERE o.ShippedDate IS NOT NULL
        GROUP BY s.CompanyName
    """, conn)
    conn.close()

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(df['Shipper'], df['TotalOrders'], color=['#4C72B0','#DD8452','#55A868'])
    ax.set_title('Số đơn hàng theo Shipper', fontsize=14)
    ax.set_xlabel('Đơn vị vận chuyển')
    ax.set_ylabel('Số đơn hàng')
    plt.tight_layout()
    return fig

# ========================
# TAB 3: DỰ BÁO AI
# ========================
def train_model():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT o.ShipVia, o.ShipCountry,
               DATEDIFF(day, o.OrderDate, o.ShippedDate) AS DeliveryDays
        FROM Orders o
        WHERE o.ShippedDate IS NOT NULL AND o.OrderDate IS NOT NULL
    """, conn)
    conn.close()

    df = df.dropna(subset=['DeliveryDays'])
    le = LabelEncoder()
    df['ShipCountry_encoded'] = le.fit_transform(df['ShipCountry'])

    X = df[['ShipVia', 'ShipCountry_encoded']]
    y = df['DeliveryDays']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    r2  = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)

    return model, le, r2, mae, mse

model, le, r2, mae, mse = train_model()

def predict_delivery(shipper_id, country):
    try:
        country_encoded = le.transform([country])[0]
        pred = model.predict([[int(shipper_id), country_encoded]])[0]
        result = f"📦 Dự báo thời gian giao hàng: **{pred:.1f} ngày**\n\n"
        result += f"📊 Chỉ số mô hình: R²={r2:.4f} | MAE=±{mae:.2f} ngày | MSE={mse:.2f}"
        return result
    except Exception as e:
        return f"❌ Lỗi: {str(e)}\nVui lòng kiểm tra Shipper ID (1-3) và tên quốc gia đúng chính tả."

# ========================
# GIAO DIỆN GRADIO
# ========================
with gr.Blocks(title="Hệ thống Quản lý Vận chuyển") as app:
    gr.Markdown("# 🚚 Hệ thống Quản lý Vận chuyển & Dự báo Thời gian Giao hàng")
    gr.Markdown("Đồ án môn Lập trình Python | Sinh viên: Huỳnh Đức Trọng")

    with gr.Tab("📋 Quản lý Đơn hàng"):
        gr.Markdown("### Danh sách đơn hàng từ CSDL Northwind")
        btn_load = gr.Button("🔄 Tải dữ liệu", variant="primary")
        table = gr.DataFrame()
        btn_load.click(fn=show_orders, outputs=table)

    with gr.Tab("📊 Thống kê"):
        gr.Markdown("### Biểu đồ so sánh hiệu suất Shipper")
        btn_chart = gr.Button("📈 Vẽ biểu đồ", variant="primary")
        chart = gr.Plot()
        btn_chart.click(fn=show_chart, outputs=chart)

    with gr.Tab("🤖 Dự báo AI"):
        gr.Markdown("### Dự báo số ngày giao hàng bằng Linear Regression")
        with gr.Row():
            shipper = gr.Dropdown(choices=["1","2","3"], label="Shipper ID", value="1")
            country = gr.Textbox(label="Quốc gia (tiếng Anh)", placeholder="VD: Germany, France, Brazil...")
        btn_predict = gr.Button("🔮 Dự báo", variant="primary")
        result = gr.Markdown()
        btn_predict.click(fn=predict_delivery, inputs=[shipper, country], outputs=result)

app.launch(server_name="0.0.0.0", server_port=7860)
