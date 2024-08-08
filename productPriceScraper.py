import requests
from bs4 import BeautifulSoup
import smtplib
import schedule
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize the Firebase app
cred = credentials.Certificate(r'C:\Users\sopra\Downloads\price-watcher-2432b-firebase-adminsdk-obq4w-bb2cfaac56.json')
firebase_admin.initialize_app(cred)

# Initialize Firestore DB
db = firestore.client()

username = "rloveumom@gmail.com"
password = "pbjg bmgr uitp jnhr"

def sendMail(link, old_price, new_price, level):
    server = "smtp.gmail.com"
    port = 587
    s = smtplib.SMTP(host=server, port=port)
    s.starttls()
    s.login(username, password)

    msg = MIMEMultipart()
    msg["To"] = "rpranav1820@gmail.com"
    msg["From"] = username
    msg["Subject"] = "Price has changed"
    text = f"""<p>The price for <a href='{link}'>this item</a> has changed from {old_price} to {new_price}. Your set level is {level}.</p>"""
    msg.attach(MIMEText(text, 'html'))
    s.send_message(msg)
    del msg

def parse_price(price_str):
    # Remove currency symbol and any whitespace
    price_str = price_str.strip()[4:]
    # Remove commas
    price_str = price_str.replace(',', '')
    # Convert to float
    return float(price_str)

def check_price():
    products_ref = db.collection("product")
    products = products_ref.stream()

    for product in products:
        product_data = product.to_dict()
        link = product_data['link']
        old_price = product_data['price']
        level = product_data['level']

        try:
            response = requests.get(link)
            response.raise_for_status()
            html = response.text
                
            soup = BeautifulSoup(html, "html.parser")
                
            # Adjust the selector to match the actual structure of the webpage
            myPrice = soup.find("span", {"id": "ProductPrice-8167267041531"})
                
            if myPrice:
                price_text = myPrice.get_text(strip=True)
                current_price = parse_price(price_text)
                if current_price != old_price:
                    # Update price in db
                    products_ref.document(product.id).update({"price": current_price})
                    print(f"Updated price for {link} from {old_price} to {current_price}")
                    sendMail(link, old_price, current_price, level)
            else:
                print(f"Price element not found for {link}")
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {link}: {e}")
        except ValueError as e:
            print(f"Error parsing price for {link}: {e}")
        except Exception as e:
            print(f"An error occurred for {link}: {e}")

def add_product(link, level):
    try:
        response = requests.get(link)
        response.raise_for_status()
        html = response.text
        
        soup = BeautifulSoup(html, "html.parser")
        
        myPrice = soup.find("span", {"id": "ProductPrice-8167267041531"})
        
        if myPrice:
            price_text = myPrice.get_text(strip=True)
            current_price = parse_price(price_text)
            
            doc_ref = db.collection("product").document()
            doc_ref.set({
                "link": link,
                "price": current_price,
                "level": level
            })
            print(f"Added new product with current price {current_price}")
        else:
            print("Price element not found")
    
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except ValueError as e:
        print(f"Error parsing price: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    while True:
        link = input("Enter the product link (or 'q' to quit): ")
        if link.lower() == 'q':
            break
        
        level = float(input("Enter the price level to watch for: "))
        
        add_product(link, level)
    
    schedule.every().day.at("10:00").do(check_price)
    
    print("Daily price checks scheduled for 10:00 AM. Press Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping scheduled checks.")

if __name__ == '__main__':    
    main()