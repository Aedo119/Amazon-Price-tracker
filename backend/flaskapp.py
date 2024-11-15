import threading
from datetime import datetime
import requests
import random
from bs4 import BeautifulSoup
import pandas as pd
import smtplib
import os
import time
from flask import Flask, jsonify, request
from flask_cors import CORS  # Import CORS
from apscheduler.schedulers.background import BackgroundScheduler  # Import APScheduler


scheduler = BackgroundScheduler()
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes by default


@app.route('/')
def home():
    return "Flask Server is running!"

def scrape_product_data(url):
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    ]
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        # Send the GET request
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Will raise an exception for any HTTP error (e.g., 404)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract product details safely
        product_name = soup.find(id='productTitle')
        product_name = product_name.get_text(strip=True) if product_name else "Product name not found"

        price = soup.find('span', {'class': 'a-price-whole'})
        price_value = price.get_text(strip=True) if price else "Price not found"

        availability = soup.find("div", attrs={'id': 'availability'})
        availability_text = availability.find("span").string.strip() if availability and availability.find(
            "span") else "Availability not found"

        # Extract product image URL
        image_div = soup.find("div", id="imgTagWrapperId")
        image_url = image_div.img['src'] if image_div and image_div.img else "Image not found"

        return product_name, price_value, image_url,availability_text == "In stock"

    except requests.RequestException as e:
        print("Error fetching the product page:", e)
        return None

# Function to send email alerts
def send_email_alert(to_email, product_name, price_value):
    from_email = "your_email"  # Use just the email here
    display_name = "SnakeBytes"  # Set the display name separately
    app_password = "your_password"  # Use the App Password you created

    subject = f"Price Drop Alert for {product_name}"
    body = f"The price of '{product_name}' has dropped to {price_value}!"
    # Format the message with the From header including the display name
    message = f"Subject: {subject}\nFrom: {display_name} <{from_email}>\n\n{body}"

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(from_email, app_password)  # Keep the email-only address here
            server.sendmail(from_email, to_email, message)
        print("Email alert sent successfully.")
    except Exception as e:
        print(f"Failed to send email alert: {e}")


# API route to scrape product data
@app.route('/scrape', methods=['POST'])
def api_scrape():
    data = request.get_json()
    url = data['url']
    email = data.get('email', None)
    threshval = data.get('threshval', None)

    product_name, price_value,image_url, available = scrape_product_data(url)

    if product_name and price_value:
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        price_value_float = float(price_value.replace(',', '').replace('₹', '').strip())

        # Save to CSV
        save_to_csv([(current_time, product_name, price_value_float, available,image_url)], url, email, threshval)
        return jsonify({"status": "success", "product_name": product_name, "price": price_value, "available": available})

    else:
        return jsonify({"status": "error", "message": "Failed to scrape the website. Please check the URL."})

# Function to save data to CSV
def save_to_csv(data, url, email=None, threshval=None):
    directory = "amazon_prices"
    if not os.path.exists(directory):
        os.makedirs(directory)

    url_part = url[-10:]
    csv_file = os.path.join(directory, f"price_history_{url_part}.csv")
    file_exists = os.path.isfile(csv_file)

    # Create a DataFrame from the input data
    df = pd.DataFrame(data, columns=['Date', 'Product', 'Price', 'Available','image_url'])

    # If the file exists and the threshold value is None, read the last threshold
    if threshval is None and file_exists:
        existing_df = pd.read_csv(csv_file)
        # Fetch the last threshold value from the most recent row
        last_row = existing_df.iloc[-1]
        threshval = last_row['Threshold']


    df['Threshold'] = threshval
    if email is None and file_exists:
        existing_df = pd.read_csv(csv_file)

        last_row = existing_df.iloc[-1]
        email = last_row['email']

    df['email'] = email
    latest_price = df['Price'].iloc[-1]  # Get the price of the most recent entry
    if latest_price < float(threshval):  # Assuming you want to alert for a drop in price
        send_email_alert(email, df['Product'].iloc[-1], latest_price)

    # Append the new data to the CSV file
    df.to_csv(csv_file, mode='a', header=not file_exists, index=False)

# Main function to run the Flask app
def run_flask_app():
    app.run(port=5000, use_reloader=False)

# Start Flask app in a separate thread
threading.Thread(target=run_flask_app, daemon=True).start()

#to plot graph
@app.route('/price-trend', methods=['POST'])
def price_trend():
    data = request.get_json()
    url = data.get('url')
    url_part = url[-10:]

    try:
        csv_path = f"amazon_prices/price_history_{url_part}.csv"

        if not os.path.exists(csv_path):
            return jsonify({"error": "Data not found for the given URL."}), 404

        df = pd.read_csv(csv_path, on_bad_lines='skip')

        # Ensure 'Date' and 'Price' columns are present
        if 'Date' not in df.columns or 'Price' not in df.columns:
            return jsonify({"error": "Invalid data format in CSV."}), 400

        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])

        # Prepare data for JSON response
        date_price_data = {
            "dates": df['Date'].dt.strftime('%Y-%m-%d').tolist(),
            "prices": df['Price'].tolist()
        }

        return jsonify(date_price_data)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "An error occurred while processing the data."}), 500

@app.route('/history', methods=['POST'])
def get_price_history():
    data = request.json
    url_part = data.get("url_part")

    file_path = f"amazon_prices/price_history_{url_part}.csv"
    if not os.path.exists(file_path):
        return jsonify({"status": "error", "message": "No history available for this product."})

    # Read price history from CSV
    df = pd.read_csv(file_path, on_bad_lines='skip')
    if df.empty:
        return jsonify({"status": "error", "message": "No data available in the history file."})

    # Prepare data for frontend
    history_data = {
        "dates": df['Date'].tolist(),
        "prices": df['Price'].tolist()
    }
    return jsonify({"status": "success", "history_data": history_data})
@app.route('/tracked-products', methods=['GET'])
def get_tracked_products():
    directory = "amazon_prices"
    products = []

    if os.path.exists(directory):
        for file in os.listdir(directory):
            if file.endswith(".csv"):
                url_part = os.path.splitext(file)[0].split("_")[2]  # Extract product ID
                file_path = os.path.join(directory, file)

                # Load product name from the CSV file
                df = pd.read_csv(file_path, on_bad_lines='skip')
                product_name = df['Product'][0] if not df.empty else "Unknown Product"
                image_url=df['image_url'][0]
                # Append product details to the list
                products.append({"id": url_part, "name": product_name,"image_url":image_url})

    return jsonify({"status": "success", "products": products})

@app.route('/delete-history', methods=['DELETE'])
def delete_product_history():

    data = request.get_json()
    product_id=data.get('product_id')
    csv_file = os.path.join("amazon_prices", f"price_history_{product_id}.csv")
    print(csv_file)
    if os.path.exists(csv_file):
        os.remove(csv_file)
        return jsonify({"status": "success", "message": "All product histories have been deleted."})
    else:
        return jsonify({"status": "error", "message": "file doesnt exist."})

def update_prices_for_all_products():
    directory = "amazon_prices"
    if os.path.exists(directory):
        for file in os.listdir(directory):
            if file.endswith(".csv"):
                file_path = os.path.join(directory, file)
                # Extract the product URL part (last 10 characters)
                product_id = file.split("_")[-1].split(".")[0]
                url = f"https://www.amazon.in/dp/{product_id}"

                # Scrape and update price
                product_name, price_value, image_url, available = scrape_product_data(url)
                if product_name and price_value:
                    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                    price_value_float = float(price_value.replace(',', '').replace('₹', '').strip())


                    save_to_csv([(current_time, product_name, price_value_float, available, image_url)], url)



# Schedule the job to run every 30 minutes
scheduler.add_job(update_prices_for_all_products, 'interval', minutes=120,start_date=datetime.now())
scheduler.start()



if __name__ == "__main__":
    run_flask_app()
