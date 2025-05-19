import customtkinter as ctk
import tkinter.messagebox as mb
import mysql.connector
from mysql.connector import Error
from tkinter import ttk
from contextlib import contextmanager
import tkinter as tk
import re
from datetime import datetime
import pytz

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

@contextmanager
def db_cursor():
    connection = None
    cursor = None
    try:
        connection = connect_db()
        cursor = connection.cursor(buffered=True)  
        yield cursor
        connection.commit()
    except Error as e:
        if connection:
            connection.rollback()
        mb.showerror("Database Error", f"Database error: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def connect_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="password",
            database="SportsTicketing"
        )
        if connection.is_connected():
            return connection
    except Error as e:
        raise ConnectionError(f"Unable to connect to MySQL: {e}")

def AddOffice(name, address):
    with db_cursor() as cursor:
        query = "INSERT INTO BoxOffices (OfficeName, Address) VALUES (%s, %s)"
        cursor.execute(query, (name, address))
        mb.showinfo("Success", "Office added successfully!")

class RoleSelector(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")  
        self.app = app
        self.pack(expand=True, fill="both")  

      
        ctk.CTkLabel(
            self,
            text="Sports Ticketing System\nSelect Your Role",
            font=("Arial", 28, "bold"),
            text_color="#FFFFFF"  
        ).pack(pady=(50, 30))

       
        role_styles = {
            "Admin": {"hover_color": "#66D9FF"}, 
            "Manager": {"hover_color": "#66D9FF"},  
            "Cashier": { "hover_color": "#66D9FF"}  
        }

        for role in ["Admin", "Manager", "Cashier"]:
            ctk.CTkButton(
                self,
                text=role,
                font=("Arial", 20),
                width=300,  
                height=60,  
                corner_radius=10,  
                fg_color=role_styles[role]["hover_color"],
                hover_color=role_styles[role]["hover_color"],
                text_color="#000000",
                command=lambda r=role: self.app.show_role_page(r)
            ).pack(pady=15)


class AdminPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.pack()

        self.tree_frame = ctk.CTkFrame(self)
        self.tree_frame.pack(pady=10, fill="both", expand=True)

        self.office_tree = ttk.Treeview(self.tree_frame, columns=("ID", "Name", "Address"), show="headings", height=10)
        self.office_tree.heading("ID", text="ID")
        self.office_tree.heading("Name", text="Office Name")
        self.office_tree.heading("Address", text="Address")
        self.office_tree.column("ID", width=50)
        self.office_tree.column("Name", width=200)
        self.office_tree.column("Address", width=300)
        self.office_tree.pack(side="left", fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.office_tree.yview)
        self.office_tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")

        self.name_entry = ctk.CTkEntry(self, placeholder_text="Office Name")
        self.name_entry.pack(pady=5)
        self.addr_entry = ctk.CTkEntry(self, placeholder_text="Address")
        self.addr_entry.pack(pady=5)

        self.new_addr_entry = ctk.CTkEntry(self, placeholder_text="New Address for Update", width=200)
        self.new_addr_entry.pack(pady=5)

        ctk.CTkButton(self, text="Add Office", command=self.add_office).pack(pady=5)
        ctk.CTkButton(self, text="Clear", command=self.clear_form).pack(pady=5)
        ctk.CTkButton(self, text="Remove Selected Office", command=self.remove_selected_office).pack(pady=5)
        ctk.CTkButton(self, text="Update Office Address", command=self.update_office_address).pack(pady=5)
        ctk.CTkButton(self, text="Logout", command=lambda: self.master.show_role_page("Role")).pack(pady=10)

        self.refresh()

    def refresh(self):
        for item in self.office_tree.get_children():
            self.office_tree.delete(item)
        try:
            with db_cursor() as cursor:
                cursor.execute("SELECT BoxOfficeID, OfficeName, Address FROM BoxOffices")
                for row in cursor.fetchall():
                    self.office_tree.insert("", "end", values=(row[0], row[1], row[2]))
        except Exception as e:
            mb.showerror("Error", f"Unable to load office list: {e}")

    def add_office(self):
        name = self.name_entry.get().strip()
        address = self.addr_entry.get().strip()
        if not name or not address:
            mb.showerror("Input Error", "Please enter both name and address.")
            return
        try:
            AddOffice(name, address)
            self.refresh()
            self.clear_form()
        except Exception as e:
            mb.showerror("Error", f"Unable to add office: {e}")

    def clear_form(self):
        self.name_entry.delete(0, 'end')
        self.addr_entry.delete(0, 'end')
        self.new_addr_entry.delete(0, 'end')

    def remove_selected_office(self):
        selected = self.office_tree.selection()
        if not selected:
            mb.showerror("Selection Error", "Please select an office to remove.")
            return
        try:
            box_office_id = self.office_tree.item(selected[0])["values"][0]
            with db_cursor() as cursor:
                cursor.execute("DELETE FROM BoxOffices WHERE BoxOfficeID = %s", (box_office_id,))
            self.refresh()
            mb.showinfo("Success", "Office removed successfully!")
        except Exception as e:
            mb.showerror("Error", f"Unable to remove office: {e}")

    def update_office_address(self):
        selected = self.office_tree.selection()
        if not selected:
            mb.showerror("Selection Error", "Please select an office to update the address.")
            return
        new_address = self.new_addr_entry.get().strip()
        if not new_address:
            mb.showerror("Input Error", "Please enter a new address.")
            return
        try:
            box_office_id = self.office_tree.item(selected[0])["values"][0]
            with db_cursor() as cursor:
                cursor.execute("UPDATE BoxOffices SET Address = %s WHERE BoxOfficeID = %s", (new_address, box_office_id))
            self.refresh()
            self.new_addr_entry.delete(0, 'end')
            mb.showinfo("Success", f"Office address updated to {new_address} successfully!")
        except Exception as e:
            mb.showerror("Error", f"Unable to update office address: {e}")

class ManagerPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.pack()

        self.tree_frame = ctk.CTkFrame(self)
        self.tree_frame.pack(pady=10, fill="both", expand=True)

        self.event_tree = ttk.Treeview(self.tree_frame, columns=(
            "ID", "Name", "Date", "Venue", "VIP Seats", "Premium Seats", "Standard Seats"
        ), show="headings", height=10)
        self.event_tree.heading("ID", text="ID")
        self.event_tree.heading("Name", text="Name")
        self.event_tree.heading("Date", text="Date")
        self.event_tree.heading("Venue", text="Venue")
        self.event_tree.heading("VIP Seats", text="VIP Seats (Avl)")
        self.event_tree.heading("Premium Seats", text="Premium Seats (Avl)")
        self.event_tree.heading("Standard Seats", text="Standard Seats (Avl)")
        self.event_tree.column("ID", width=50)
        self.event_tree.column("Name", width=150)
        self.event_tree.column("Date", width=100)
        self.event_tree.column("Venue", width=150)
        self.event_tree.column("VIP Seats", width=100)
        self.event_tree.column("Premium Seats", width=120)
        self.event_tree.column("Standard Seats", width=120)
        self.event_tree.pack(side="left", fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.event_tree.yview)
        self.event_tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")

        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(pady=10)

        self.name = ctk.CTkEntry(self.input_frame, placeholder_text="Event Name", width=250)
        self.date = ctk.CTkEntry(self.input_frame, placeholder_text="Date (YYYY-MM-DD)", width=250)
        self.venue = ctk.CTkEntry(self.input_frame, placeholder_text="Venue", width=250)

        self.vip_price = ctk.CTkEntry(self.input_frame, placeholder_text="VIP Price", width=120)
        self.vip_qty = ctk.CTkEntry(self.input_frame, placeholder_text="VIP Quantity", width=120)
        self.premium_price = ctk.CTkEntry(self.input_frame, placeholder_text="Premium Price", width=120)
        self.premium_qty = ctk.CTkEntry(self.input_frame, placeholder_text="Premium Quantity", width=120)
        self.standard_price = ctk.CTkEntry(self.input_frame, placeholder_text="Standard Price", width=120)
        self.standard_qty = ctk.CTkEntry(self.input_frame, placeholder_text="Standard Quantity", width=120)

        self.name.grid(row=0, column=0, padx=5, pady=5, columnspan=2, sticky="ew")
        self.date.grid(row=1, column=0, padx=5, pady=5, columnspan=2, sticky="ew")
        self.venue.grid(row=2, column=0, padx=5, pady=5, columnspan=2, sticky="ew")
        self.vip_price.grid(row=3, column=0, padx=5, pady=5, sticky="ew")
        self.vip_qty.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.premium_price.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
        self.premium_qty.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        self.standard_price.grid(row=5, column=0, padx=5, pady=5, sticky="ew")
        self.standard_qty.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(pady=10)

        ctk.CTkButton(self.button_frame, text="Add Event", command=self.add_event).grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkButton(self.button_frame, text="Remove Selected Event", command=self.remove_selected_event).grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(self.button_frame, text="Clear Form", command=self.clear_form).grid(row=0, column=2, padx=5, pady=5)
        ctk.CTkButton(self.button_frame, text="View Report", command=self.view_report).grid(row=0, column=3, padx=5, pady=5)
        ctk.CTkButton(self.button_frame, text="Edit Event Date", command=self.edit_event_date).grid(row=0, column=4, padx=5, pady=5)
        self.new_date = ctk.CTkEntry(self.button_frame, placeholder_text="New Date (YYYY-MM-DD)", width=150)
        self.new_date.grid(row=0, column=5, padx=5, pady=5)
        ctk.CTkButton(self.button_frame, text="Logout", command=lambda: self.master.show_role_page("Role")).grid(row=0, column=6, padx=5, pady=5)

        self.refresh()

    def refresh(self):
        for item in self.event_tree.get_children():
            self.event_tree.delete(item)
        try:
            with db_cursor() as cursor:
                cursor.execute("""
                    SELECT e.EventID, e.EventName, e.EventDate, e.Venue,
                           IFNULL(SUM(CASE WHEN s.SeatType = 'VIP' THEN 1 ELSE 0 END),0) AS VIP_Seats,
                           IFNULL(SUM(CASE WHEN s.SeatType = 'Premium' THEN 1 ELSE 0 END),0) AS Premium_Seats,
                           IFNULL(SUM(CASE WHEN s.SeatType = 'Standard' THEN 1 ELSE 0 END),0) AS Standard_Seats,
                           IFNULL(SUM(CASE WHEN s.SeatType = 'VIP' AND s.Status = 'Available' THEN 1 ELSE 0 END),0) AS VIP_Available,
                           IFNULL(SUM(CASE WHEN s.SeatType = 'Premium' AND s.Status = 'Available' THEN 1 ELSE 0 END),0) AS Premium_Available,
                           IFNULL(SUM(CASE WHEN s.SeatType = 'Standard' AND s.Status = 'Available' THEN 1 ELSE 0 END),0) AS Standard_Available
                    FROM Events e
                    LEFT JOIN Seats s ON e.EventID = s.EventID
                    GROUP BY e.EventID
                    ORDER BY e.EventID
                """)
                for row in cursor.fetchall():
                    self.event_tree.insert("", "end", values=(
                        row[0], row[1], row[2], row[3],
                        f"{row[4]} ({row[7]})", f"{row[5]} ({row[8]})", f"{row[6]} ({row[9]})"
                    ))
        except Exception as e:
            mb.showerror("Error", f"Unable to load event list: {e}")

    def add_event(self):
        name = self.name.get().strip()
        date = self.date.get().strip()
        venue = self.venue.get().strip()
        if not name or not date or not venue:
            mb.showerror("Input Error", "Please enter all event details.")
            return

        try:
            vip_price = float(self.vip_price.get()) if self.vip_price.get().strip() else 0
            vip_qty = int(self.vip_qty.get()) if self.vip_qty.get().strip() else 0
            premium_price = float(self.premium_price.get()) if self.premium_price.get().strip() else 0
            premium_qty = int(self.premium_qty.get()) if self.premium_qty.get().strip() else 0
            standard_price = float(self.standard_price.get()) if self.standard_price.get().strip() else 0
            standard_qty = int(self.standard_qty.get()) if self.standard_qty.get().strip() else 0
        except ValueError:
            mb.showerror("Input Error", "Invalid price or quantity.")
            return

        try:
            with db_cursor() as cursor:
                cursor.execute("START TRANSACTION")
                cursor.execute("INSERT INTO Events (EventName, EventDate, Venue) VALUES (%s, %s, %s)",
                              (name, date, venue))
                event_id = cursor.lastrowid

                ticket_types = []
                if vip_qty > 0:
                    ticket_types.append((event_id, "VIP", vip_price, vip_qty))
                if premium_qty > 0:
                    ticket_types.append((event_id, "Premium", premium_price, premium_qty))
                if standard_qty > 0:
                    ticket_types.append((event_id, "Standard", standard_price, standard_qty))

                if ticket_types:
                    cursor.executemany(
                        "INSERT INTO EventTicketType (EventID, TicketType, Price, Quantity) VALUES (%s, %s, %s, %s)",
                        ticket_types
                    )

                seat_inserts = []
                seat_number = 1
                for _ in range(vip_qty):
                    seat_inserts.append((event_id, seat_number, 'VIP', 'Available'))
                    seat_number += 1
                for _ in range(premium_qty):
                    seat_inserts.append((event_id, seat_number, 'Premium', 'Available'))
                    seat_number += 1
                for _ in range(standard_qty):
                    seat_inserts.append((event_id, seat_number, 'Standard', 'Available'))
                    seat_number += 1

                if seat_inserts:
                    cursor.executemany(
                        "INSERT INTO Seats (EventID, SeatNumber, SeatType, Status) VALUES (%s, %s, %s, %s)",
                        seat_inserts
                    )

                cursor.execute("COMMIT")

            self.refresh()
            self.clear_form()
            mb.showinfo("Success", "Event and seats added successfully!")
        except Exception as e:
            mb.showerror("Error", f"Unable to add event: {e}")

    def remove_selected_event(self):
        selected = self.event_tree.selection()
        if not selected:
            mb.showerror("Selection Error", "Please select an event to remove.")
            return
        try:
            event_id = self.event_tree.item(selected[0])["values"][0]
            with db_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM Tickets WHERE EventID = %s", (event_id,))
                if cursor.fetchone()[0] > 0:
                    mb.showerror("Error", "Cannot delete event because it has booked tickets.")
                    return
                cursor.execute("DELETE FROM Seats WHERE EventID = %s", (event_id,))
                cursor.execute("DELETE FROM EventTicketType WHERE EventID = %s", (event_id,))
                cursor.execute("DELETE FROM Events WHERE EventID = %s", (event_id,))
            self.refresh()
            mb.showinfo("Success", f"Event ID {event_id} removed successfully!")
        except Exception as e:
            mb.showerror("Error", f"Unable to remove event: {e}")

    def clear_form(self):
        for entry in [self.name, self.date, self.venue,
                      self.vip_price, self.vip_qty,
                      self.premium_price, self.premium_qty,
                      self.standard_price, self.standard_qty]:
            entry.delete(0, 'end')

    def export_report(self, event_id, event_name):
        try:
            # Sanitize event name to create a valid filename
            sanitized_event_name = re.sub(r'[\\/:*?"<>|]', '_', event_name).replace(' ', '_')
            filename = f"{sanitized_event_name}_revenue.txt"
            
            with db_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN Tickets.TicketType = 'VIP' THEN 1 ELSE 0 END) as VIP_Tickets,
                        SUM(CASE WHEN Tickets.TicketType = 'Premium' THEN 1 ELSE 0 END) as Premium_Tickets,
                        SUM(CASE WHEN Tickets.TicketType = 'Standard' THEN 1 ELSE 0 END) as Standard_Tickets,
                        COUNT(Tickets.TicketID) as Total_Tickets,
                        SUM(Tickets.Price) as Revenue
                    FROM Tickets
                    JOIN Events ON Tickets.EventID = Events.EventID
                    WHERE Events.EventID = %s
                    GROUP BY Events.EventID
                """, (event_id,))
                data = cursor.fetchone()
                # Get real-time date using pytz
                tz = pytz.timezone("Asia/Bangkok")
                current_date = datetime.now(tz).strftime("%B %d, %Y")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"Revenue Report for {event_name}\n")
                    f.write(f"Date of Report: {current_date}\n")
                    f.write("-" * 50 + "\n")
                    if data:
                        f.write(f"VIP Tickets: {data[0] or 0}\n")
                        f.write(f"Premium Tickets: {data[1] or 0}\n")
                        f.write(f"Standard Tickets: {data[2] or 0}\n")
                        f.write(f"Total Tickets: {data[3] or 0}\n")
                        f.write(f"Revenue: {data[4] or 0}\n")
                    else:
                        f.write("No ticket sales data available for this event.\n")
            mb.showinfo("Success", f"Revenue report for '{event_name}' exported successfully to {filename}")
        except Exception as e:
            mb.showerror("Error", f"Unable to export report: {e}")

    def view_report(self):
        selected = self.event_tree.selection()
        if not selected:
            mb.showerror("Selection Error", "Please select an event from the Treeview to view the report.")
            return
        try:
            event_id = self.event_tree.item(selected[0])["values"][0]
            event_name = self.event_tree.item(selected[0])["values"][1]
            with db_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN Tickets.TicketType = 'VIP' THEN 1 ELSE 0 END) as VIP_Tickets,
                        SUM(CASE WHEN Tickets.TicketType = 'Premium' THEN 1 ELSE 0 END) as Premium_Tickets,
                        SUM(CASE WHEN Tickets.TicketType = 'Standard' THEN 1 ELSE 0 END) as Standard_Tickets,
                        COUNT(Tickets.TicketID) as Total_Tickets,
                        SUM(Tickets.Price) as Revenue
                    FROM Tickets
                    JOIN Events ON Tickets.EventID = Events.EventID
                    WHERE Events.EventID = %s
                    GROUP BY Events.EventID
                """, (event_id,))
                data = cursor.fetchone()

            report_window = tk.Toplevel(self)
            report_window.title(f"Revenue Report - {event_name}")
            report_window.geometry("600x300")

            tree_frame = ttk.Frame(report_window)
            tree_frame.pack(pady=10, fill="both", expand=True)

            report_tree = ttk.Treeview(tree_frame, columns=(
                "Event", "VIP Tickets", "Premium Tickets", "Standard Tickets", "Total Tickets", "Revenue"
            ), show="headings", height=1)
            report_tree.heading("Event", text="Event")
            report_tree.heading("VIP Tickets", text="VIP Tickets")
            report_tree.heading("Premium Tickets", text="Premium Tickets")
            report_tree.heading("Standard Tickets", text="Standard Tickets")
            report_tree.heading("Total Tickets", text="Total Tickets")
            report_tree.heading("Revenue", text="Revenue")
            report_tree.column("Event", width=150)
            report_tree.column("VIP Tickets", width=100)
            report_tree.column("Premium Tickets", width=100)
            report_tree.column("Standard Tickets", width=100)
            report_tree.column("Total Tickets", width=100)
            report_tree.column("Revenue", width=100)
            report_tree.pack(side="left", fill="both", expand=True)

            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=report_tree.yview)
            report_tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")

            if data:
                report_tree.insert("", "end", values=(
                    event_name, data[0] or 0, data[1] or 0, data[2] or 0, data[3] or 0, data[4] or 0
                ))
            else:
                report_tree.insert("", "end", values=(
                    event_name, 0, 0, 0, 0, 0
                ))
                mb.showinfo("No Data", "No ticket sales data available for this event.")

            button_frame = ctk.CTkFrame(report_window, fg_color="transparent")
            button_frame.pack(pady=10)
            ctk.CTkButton(button_frame, text="Export Revenue Report", fg_color="white", text_color="#000000", 
                          command=lambda: self.export_report(event_id, event_name)).pack(side="left", padx=5)
            ctk.CTkButton(button_frame, text="Close", fg_color="white", text_color="#000000", 
                          command=report_window.destroy).pack(side="left", padx=5)

        except Exception as e:
            mb.showerror("Error", f"Unable to view report: {e}")

    def edit_event_date(self):
        selected = self.event_tree.selection()
        if not selected:
            mb.showerror("Selection Error", "Please select an event to edit the date.")
            return
        new_date = self.new_date.get().strip()
        if not new_date:
            mb.showerror("Input Error", "Please enter a new date in YYYY-MM-DD format.")
            return
        try:
            # Validate date format
            datetime.strptime(new_date, "%Y-%m-%d")
        except ValueError:
            mb.showerror("Input Error", "Invalid date format. Use YYYY-MM-DD.")
            return

        try:
            event_id = self.event_tree.item(selected[0])["values"][0]
            with db_cursor() as cursor:
                cursor.execute("UPDATE Events SET EventDate = %s WHERE EventID = %s", (new_date, event_id))
            self.refresh()
            self.new_date.delete(0, 'end')
            mb.showinfo("Success", f"Event date updated to {new_date} successfully!")
        except Exception as e:
            mb.showerror("Error", f"Unable to update event date: {e}")

class CashierPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.pack()

        # Customer Treeview Section (Moved to Top)
        self.tree_frame = ctk.CTkFrame(self)
        self.tree_frame.pack(pady=10, fill="both", expand=True)

        self.customer_tree = ttk.Treeview(self.tree_frame, columns=(
            "ID", "Name", "Phone", "Address", "Event", "Type", "Seat", "Price"
        ), show="headings", height=10)
        self.customer_tree.heading("ID", text="ID")
        self.customer_tree.heading("Name", text="Customer Name")
        self.customer_tree.heading("Phone", text="Phone")
        self.customer_tree.heading("Address", text="Address")
        self.customer_tree.heading("Event", text="Event Name")
        self.customer_tree.heading("Type", text="Ticket Type")
        self.customer_tree.heading("Seat", text="Seat Number")
        self.customer_tree.heading("Price", text="Price")
        self.customer_tree.column("ID", width=50)
        self.customer_tree.column("Name", width=150)
        self.customer_tree.column("Phone", width=100)
        self.customer_tree.column("Address", width=150)
        self.customer_tree.column("Event", width=150)
        self.customer_tree.column("Type", width=100)
        self.customer_tree.column("Seat", width=80)
        self.customer_tree.column("Price", width=80)
        self.customer_tree.pack(side="left", fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.customer_tree.yview)
        self.customer_tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")

        # Main frame for columnar layout (Moved below Treeview)
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(pady=10, fill="both", expand=False)

        # Add Customer Section (Column 0)
        self.add_customer_frame = ctk.CTkFrame(self.main_frame)
        self.add_customer_frame.grid(row=0, column=0, padx=10, pady=5, sticky="n")

        ctk.CTkLabel(self.add_customer_frame, text="Add Customer", font=("Arial", 14)).pack(pady=5)

        self.name = ctk.CTkEntry(self.add_customer_frame, placeholder_text="Customer Name", width=200)
        self.phone = ctk.CTkEntry(self.add_customer_frame, placeholder_text="Phone", width=200)
        self.addr = ctk.CTkEntry(self.add_customer_frame, placeholder_text="Address", width=200)

        self.name.pack(pady=2)
        self.phone.pack(pady=2)
        self.addr.pack(pady=2)

        ctk.CTkButton(self.add_customer_frame, text="Add Customer", command=self.add_customer).pack(pady=5)

        # Remove Ticket Section (Column 1)
        self.remove_ticket_frame = ctk.CTkFrame(self.main_frame)
        self.remove_ticket_frame.grid(row=0, column=1, padx=10, pady=5, sticky="n")

        ctk.CTkLabel(self.remove_ticket_frame, text="Cancel Ticket", font=("Arial", 14)).pack(pady=5)
        ctk.CTkButton(self.remove_ticket_frame, text="Cancel Selected Ticket", command=self.remove_selected_ticket).pack(pady=5)

        # Remove Customer Section (Column 1, below Remove Ticket)
        self.remove_customer_frame = ctk.CTkFrame(self.main_frame)
        self.remove_customer_frame.grid(row=0, column=1, padx=10, pady=100, sticky="n")

        ctk.CTkLabel(self.remove_customer_frame, text="Remove Customer", font=("Arial", 14)).pack(pady=5)
        ctk.CTkButton(self.remove_customer_frame, text="Remove Selected Customer", command=self.remove_customer).pack(pady=5)

        # Book Ticket Section (Column 2)
        self.book_ticket_frame = ctk.CTkFrame(self.main_frame)
        self.book_ticket_frame.grid(row=0, column=2, padx=10, pady=5, sticky="n")

        ctk.CTkLabel(self.book_ticket_frame, text="Book Ticket", font=("Arial", 14)).pack(pady=5)

        self.book_inputs_frame = ctk.CTkFrame(self.book_ticket_frame)
        self.book_inputs_frame.pack(pady=5)

        self.customer_entry = ctk.CTkEntry(self.book_inputs_frame, placeholder_text="Customer Phone Number", width=200)
        self.customer_entry.grid(row=0, column=0, padx=5, pady=2, sticky="ew")

        self.customer_button_frame = ctk.CTkFrame(self.book_inputs_frame)
        self.customer_button_frame.grid(row=1, column=0, padx=5, pady=2, sticky="ew")
        ctk.CTkButton(self.customer_button_frame, text="Search Customer", command=self.search_customer).pack(side="left", padx=2)
        ctk.CTkButton(self.customer_button_frame, text="View Tickets", command=self.view_customer_tickets).pack(side="left", padx=2)

        self.customer_info = ctk.CTkLabel(self.book_inputs_frame, text="Customer Info: Not selected")
        self.customer_info.grid(row=2, column=0, padx=5, pady=2)

        self.event_entry = ctk.CTkEntry(self.book_inputs_frame, placeholder_text="Event Name", width=200)
        self.event_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        ctk.CTkButton(self.book_inputs_frame, text="Search Event", command=self.search_event).grid(row=1, column=1, padx=5, pady=2)
        self.event_info = ctk.CTkLabel(self.book_inputs_frame, text="Event Info: Not selected")
        self.event_info.grid(row=2, column=1, padx=5, pady=2)

        self.ttype = ttk.Combobox(self.book_ticket_frame, values=["VIP", "Premium", "Standard"], width=27)
        self.ttype.set("Select Ticket Type")
        self.ttype.pack(pady=2)
        self.ttype.bind("<<ComboboxSelected>>", self.update_seat_numbers)

        self.seat_number = ctk.CTkComboBox(self.book_ticket_frame, values=["Select Seat"], width=200)
        self.seat_number.set("Select Seat")
        self.seat_number.pack(pady=2)

        self.price_label = ctk.CTkLabel(self.book_ticket_frame, text="Price: Not calculated")
        self.price_label.pack(pady=2)

        ctk.CTkButton(self.book_ticket_frame, text="Book", command=self.book_ticket).pack(pady=5)

        # Logout Button
        ctk.CTkButton(self, text="Logout", command=lambda: self.master.show_role_page("Role")).pack(pady=10)

        self.customer_id = None
        self.customer_phone = None  
        self.event_id = None

        self.refresh_customer_tree()

    def refresh_customer_tree(self):
        for item in self.customer_tree.get_children():
            self.customer_tree.delete(item)
        try:
            with db_cursor() as cursor:
                cursor.execute("""
                    SELECT c.CustomerID, c.CustomerName, c.PhoneNumber, c.Address,
                           e.EventName, t.TicketType,
                           (SELECT s2.SeatNumber
                            FROM Seats s2
                            WHERE s2.EventID = t.EventID
                            AND s2.SeatType = t.TicketType
                            AND s2.Status = 'Booked'
                            AND (
                                SELECT COUNT(*)
                                FROM Tickets t2
                                WHERE t2.EventID = t.EventID
                                AND t2.TicketType = t.TicketType
                                AND t2.TicketID <= t.TicketID
                            ) = (
                                SELECT COUNT(*)
                                FROM Seats s3
                                WHERE s3.EventID = s2.EventID
                                AND s3.SeatType = s2.SeatType
                                AND s3.Status = 'Booked'
                                AND s3.SeatNumber <= s2.SeatNumber
                            )
                           ) AS SeatNumber,
                           t.Price
                    FROM Customers c
                    LEFT JOIN Tickets t ON c.CustomerID = t.CustomerID
                    LEFT JOIN Events e ON t.EventID = e.EventID
                    ORDER BY c.CustomerID, t.TicketID
                """)
                for row in cursor.fetchall():
                    self.customer_tree.insert("", "end", values=(
                        row[0] if row[0] else "", row[1] if row[1] else "", row[2] if row[2] else "",
                        row[3] if row[3] else "", row[4] if row[4] else "", row[5] if row[5] else "",
                        row[6] if row[6] else "", row[7] if row[7] else ""
                    ))
            self.update_idletasks()
        except Exception as e:
            mb.showerror("Error", f"Unable to refresh customer Treeview: {e}")

    def add_customer(self):
        name = self.name.get().strip()
        phone = self.phone.get().strip()
        addr = self.addr.get().strip()
        if not name or not phone or not addr:
            mb.showerror("Input Error", "Please enter all customer details.")
            return
        try:
            with db_cursor() as cursor:
                # Check if a customer with the same phone number already exists
                cursor.execute("SELECT COUNT(*) FROM Customers WHERE PhoneNumber = %s", (phone,))
                if cursor.fetchone()[0] > 0:
                    mb.showerror("Input Error", f"A customer with phone number '{phone}' already exists.")
                    return
                # If no duplicate, proceed with insertion
                cursor.execute("INSERT INTO Customers (CustomerName, PhoneNumber, Address) VALUES (%s, %s, %s)",
                              (name, phone, addr))
            mb.showinfo("Success", "Customer added successfully!")
            self.name.delete(0, 'end')
            self.phone.delete(0, 'end')
            self.addr.delete(0, 'end')
            self.refresh_customer_tree()
        except Exception as e:
            mb.showerror("Error", f"Unable to add customer: {e}")

    def remove_customer(self):
        selected = self.customer_tree.selection()
        if not selected:
            mb.showerror("Selection Error", "Please select a customer from the Treeview to remove.")
            return
        try:
            customer_id = self.customer_tree.item(selected[0])["values"][0]
            if not customer_id:
                mb.showerror("Error", "Selected customer has no valid ID.")
                return

            with db_cursor() as cursor:
                cursor.execute("START TRANSACTION")
                # Check if the customer has any booked tickets
                cursor.execute("SELECT COUNT(*) FROM Tickets WHERE CustomerID = %s", (customer_id,))
                ticket_count = cursor.fetchone()[0]
                if ticket_count > 0:
                    cursor.execute("ROLLBACK")
                    mb.showerror("Error", "Cannot remove customer because they have booked tickets.")
                    return

                # Remove the customer if no tickets exist
                cursor.execute("DELETE FROM Customers WHERE CustomerID = %s", (customer_id,))
                cursor.execute("COMMIT")

            mb.showinfo("Success", f"Customer with ID {customer_id} removed successfully!")
            self.refresh_customer_tree()
            # Clear the selection after removal
            self.customer_tree.selection_remove(selected)

        except Exception as e:
            mb.showerror("Error", f"Unable to remove customer: {e}")

    def search_customer(self):
        customer_phone_input = self.customer_entry.get().strip()
        if not customer_phone_input:
            mb.showerror("Input Error", "Please enter a customer phone number.")
            return
        try:
            # Ensure Treeview is up-to-date
            self.refresh_customer_tree()

            with db_cursor() as cursor:
                cursor.execute("SELECT CustomerID, CustomerName, PhoneNumber FROM Customers WHERE PhoneNumber = %s",
                              (customer_phone_input,))
                customer = cursor.fetchone()
                if not customer:
                    mb.showerror("Error", f"Customer not found with phone number: {customer_phone_input}")
                    self.customer_info.configure(text="Customer Info: Not found")
                    self.customer_id = None
                    self.customer_phone = None
                    # Clear any existing selection in the Treeview
                    self.customer_tree.selection_remove(self.customer_tree.selection())
                    return
                self.customer_id = customer[0]
                self.customer_phone = customer[2]
                self.customer_info.configure(text=f"Customer: {customer[1]} (Phone: {customer[2]})")

            # Find and highlight the customer in the Treeview
            found = False
            for item in self.customer_tree.get_children():
                values = self.customer_tree.item(item)["values"]
                if values and values[0] == self.customer_id:
                    self.customer_tree.selection_set(item)  # Highlight the item
                    self.customer_tree.focus(item)          # Set focus to the item
                    self.customer_tree.see(item)            # Scroll to make the item visible
                    found = True
                    break

            if not found:
                mb.showinfo("Info", "Customer found but has no tickets to display in the Treeview.")
                self.customer_tree.selection_remove(self.customer_tree.selection())

        except Exception as e:
            mb.showerror("Error", f"Unable to search for customer: {e}")
            self.customer_id = None
            self.customer_phone = None
            self.customer_tree.selection_remove(self.customer_tree.selection())

    def view_customer_tickets(self):
        if not self.customer_id:
            mb.showerror("Input Error", "Please select a valid customer first.")
            return
        try:
            with db_cursor() as cursor:
                cursor.execute("""
                    SELECT e.EventName, t.TicketType,
                           (SELECT s2.SeatNumber
                            FROM Seats s2
                            WHERE s2.EventID = t.EventID
                            AND s2.SeatType = t.TicketType
                            AND s2.Status = 'Booked'
                            AND (
                                SELECT COUNT(*)
                                FROM Tickets t2
                                WHERE t2.EventID = t.EventID
                                AND t2.TicketType = t.TicketType
                                AND t2.TicketID <= t.TicketID
                            ) = (
                                SELECT COUNT(*)
                                FROM Seats s3
                                WHERE s3.EventID = s2.EventID
                                AND s3.SeatType = s2.SeatType
                                AND s3.Status = 'Booked'
                                AND s3.SeatNumber <= s2.SeatNumber
                            )
                           ) AS SeatNumber,
                           t.Price
                    FROM Tickets t
                    JOIN Events e ON t.EventID = e.EventID
                    WHERE t.CustomerID = %s
                    ORDER BY e.EventName
                """, (self.customer_id,))
                tickets = cursor.fetchall()

            ticket_window = tk.Toplevel(self)
            ticket_window.title("Customer Tickets")
            ticket_window.geometry("600x400")

            tree_frame = ttk.Frame(ticket_window)
            tree_frame.pack(pady=10, fill="both", expand=True)

            ticket_tree = ttk.Treeview(tree_frame, columns=("Event", "Type", "Seat", "Price"), show="headings", height=15)
            ticket_tree.heading("Event", text="Event Name")
            ticket_tree.heading("Type", text="Ticket Type")
            ticket_tree.heading("Seat", text="Seat Number")
            ticket_tree.heading("Price", text="Price")
            ticket_tree.column("Event", width=200)
            ticket_tree.column("Type", width=100)
            ticket_tree.column("Seat", width=100)
            ticket_tree.column("Price", width=100)
            ticket_tree.pack(side="left", fill="both", expand=True)

            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=ticket_tree.yview)
            ticket_tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")

            for ticket in tickets:
                ticket_tree.insert("", "end", values=(ticket[0], ticket[1], ticket[2], ticket[3]))

            ctk.CTkButton(ticket_window, text="Close", command=ticket_window.destroy).pack(pady=10)

            if not tickets:
                mb.showinfo("No Tickets", "This customer has no booked tickets.")

        except Exception as e:
            mb.showerror("Error", f"Unable to load customer tickets: {e}")

    def search_event(self):
        event_name = self.event_entry.get().strip()
        if not event_name:
            mb.showerror("Input Error", "Please enter an event name.")
            return
        try:
            with db_cursor() as cursor:
                cursor.execute("SELECT EventID, EventName, EventDate FROM Events WHERE EventName = %s",
                              (event_name,))
                event = cursor.fetchone()
                if not event:
                    mb.showerror("Error", f"Event not found: {event_name}")
                    self.event_info.configure(text="Event Info: Not found")
                    self.event_id = None
                    self.seat_number.configure(values=["Select Seat"])
                    self.seat_number.set("Select Seat")
                    return
                self.event_id = event[0]
                self.event_info.configure(text=f"Event: {event[1]} (Date: {event[2]})")
                self.update_seat_numbers(None)
        except Exception as e:
            mb.showerror("Error", f"Unable to search for event: {e}")
            self.event_id = None

    def update_seat_numbers(self, event):
        if not self.event_id or self.ttype.get() == "Select Ticket Type":
            self.seat_number.configure(values=["Select Seat"])
            self.seat_number.set("Select Seat")
            self.price_label.configure(text="Price: Not calculated")
            return
        try:
            with db_cursor() as cursor:
                cursor.execute("""
                    SELECT SeatNumber FROM Seats 
                    WHERE EventID = %s AND SeatType = %s AND Status = 'Available'
                    ORDER BY SeatNumber
                """, (self.event_id, self.ttype.get()))
                seats = [str(row[0]) for row in cursor.fetchall()]
                if not seats:
                    self.seat_number.configure(values=["No Seats Available"])
                    self.seat_number.set("No Seats Available")
                    self.price_label.configure(text="Price: Not calculated")
                else:
                    self.seat_number.configure(values=seats)
                    self.seat_number.set(seats[0])
                    self.update_price()
        except Exception as e:
            mb.showerror("Error", f"Unable to load seat list: {e}")

    def update_price(self):
        if not self.event_id or self.ttype.get() == "Select Ticket Type":
            self.price_label.configure(text="Price: Not calculated")
            return
        try:
            with db_cursor() as cursor:
                cursor.execute("""
                    SELECT Price FROM EventTicketType 
                    WHERE EventID = %s AND TicketType = %s
                """, (self.event_id, self.ttype.get()))
                price = cursor.fetchone()
                if price:
                    self.price_label.configure(text=f"Price: {price[0]}")
                else:
                    self.price_label.configure(text="Price: Not calculated")
        except Exception as e:
            mb.showerror("Error", f"Unable to retrieve ticket price: {e}")

    def book_ticket(self):
        customer_phone_input = self.customer_entry.get().strip()
        if not customer_phone_input:
            mb.showerror("Input Error", "Please enter a customer phone number.")
            return
        if not self.customer_id:
            mb.showerror("Input Error", "Please select a valid customer.")
            return
        if customer_phone_input != self.customer_phone:
            mb.showerror("Input Error", "Phone number in search box does not match selected customer.")
            return
        if not self.event_id:
            mb.showerror("Input Error", "Please select a valid event.")
            return
        ticket_type = self.ttype.get()
        seat_number = self.seat_number.get()
        if ticket_type == "Select Ticket Type" or seat_number in ["Select Seat", "No Seats Available"]:
            mb.showerror("Input Error", "Please select a valid ticket type and seat number.")
            return

        try:
            with db_cursor() as cursor:
                cursor.execute("START TRANSACTION")
                
                cursor.execute("""
                    SELECT SeatID FROM Seats 
                    WHERE EventID = %s AND SeatNumber = %s AND SeatType = %s AND Status = 'Available'
                """, (self.event_id, seat_number, ticket_type))
                seat = cursor.fetchone()
                if not seat:
                    cursor.execute("ROLLBACK")
                    mb.showerror("Error", f"Seat {seat_number} is no longer available.")
                    return
                seat_id = seat[0]

                cursor.execute("""
                    SELECT Price FROM EventTicketType 
                    WHERE EventID = %s AND TicketType = %s
                """, (self.event_id, ticket_type))
                price = cursor.fetchone()
                if not price:
                    cursor.execute("ROLLBACK")
                    mb.showerror("Error", "Ticket price information not found.")
                    return

                cursor.execute("""
                    INSERT INTO Tickets (EventID, CustomerID, TicketType, Price) 
                    VALUES (%s, %s, %s, %s)
                """, (self.event_id, self.customer_id, ticket_type, price[0]))
                ticket_id = cursor.lastrowid

                cursor.execute("""
                    UPDATE Seats 
                    SET Status = 'Booked' 
                    WHERE SeatID = %s
                """, (seat_id,))

                cursor.execute("COMMIT")

                # Fetch customer name
                cursor.execute("SELECT CustomerName FROM Customers WHERE CustomerID = %s", (self.customer_id,))
                customer = cursor.fetchone()
                if not customer:
                    mb.showerror("Error", "Customer not found.")
                    return
                customer_name = customer[0]

                # Fetch event details
                cursor.execute("SELECT EventName, EventDate FROM Events WHERE EventID = %s", (self.event_id,))
                event = cursor.fetchone()
                if not event:
                    mb.showerror("Error", "Event not found.")
                    return
                event_name, event_date = event

                # Trigger automatic ticket printing
                self.print_ticket(customer_name, self.customer_phone, event_name, event_date, ticket_type, seat_number, price[0])

            mb.showinfo("Success", "Ticket booked successfully!")
            self.customer_entry.delete(0, 'end')
            self.event_entry.delete(0, 'end')
            self.customer_info.configure(text="Customer Info: Not selected")
            self.event_info.configure(text="Event Info: Not selected")
            self.ttype.set("Select Ticket Type")
            self.seat_number.configure(values=["Select Seat"])
            self.seat_number.set("Select Seat")
            self.price_label.configure(text="Price: Not calculated")
            self.customer_id = None
            self.customer_phone = None
            self.event_id = None
            self.update_seat_numbers(None)
            self.refresh_customer_tree()
        except Exception as e:
            mb.showerror("Error", f"Unable to book ticket: {e}")

    def print_ticket(self, customer_name=None, customer_phone=None, event_name=None, event_date=None, ticket_type=None, seat_number=None, ticket_price=None):
        # Use Treeview selection if no parameters are provided
        if not customer_name or not customer_phone or not event_name or not event_date or not ticket_type or not seat_number or not ticket_price:
            selected = self.customer_tree.selection()
            if selected:
                try:
                    values = self.customer_tree.item(selected[0])["values"]
                    customer_id = values[0]
                    customer_name = values[1]
                    customer_phone = values[2] if values[2] else "Unknown"
                    event_name = values[4]
                    ticket_type = values[5]
                    seat_number = values[6]
                    ticket_price = values[7]

                    if not event_name or not ticket_type or not seat_number or not ticket_price or not customer_phone:
                        mb.showerror("Error", "Selected customer has no booked ticket to print or invalid phone number.")
                        return

                    with db_cursor() as cursor:
                        cursor.execute("SELECT EventDate FROM Events WHERE EventName = %s", (event_name,))
                        event = cursor.fetchone()
                        if not event:
                            mb.showerror("Error", "Event not found.")
                            return
                        event_date = event[0]

                except Exception as e:
                    mb.showerror("Error", f"Unable to retrieve ticket data from Treeview: {e}")
                    return
            else:
                customer_phone_input = self.customer_entry.get().strip()
                if not customer_phone_input:
                    mb.showerror("Input Error", "Please enter a customer phone number or select a customer from the Treeview.")
                    return
                if not self.customer_id:
                    mb.showerror("Input Error", "Please select a valid customer.")
                    return
                if customer_phone_input != self.customer_phone:
                    mb.showerror("Input Error", "Phone number in search box does not match selected customer.")
                    return
                if not self.event_id:
                    mb.showerror("Input Error", "Please select a valid event.")
                    return
                ticket_type = self.ttype.get()
                seat_number = self.seat_number.get()
                if ticket_type == "Select Ticket Type" or seat_number in ["Select Seat", "No Seats Available"]:
                    mb.showerror("Input Error", "Please select a valid ticket type and seat number.")
                    return

                try:
                    with db_cursor() as cursor:
                        cursor.execute("SELECT CustomerName FROM Customers WHERE CustomerID = %s",
                                      (self.customer_id,))
                        customer = cursor.fetchone()
                        if not customer:
                            mb.showerror("Error", "Customer not found.")
                            return
                        customer_name = customer[0]
                        customer_phone = self.customer_phone if self.customer_phone else "Unknown"

                        cursor.execute("SELECT EventName, EventDate FROM Events WHERE EventID = %s",
                                      (self.event_id,))
                        event = cursor.fetchone()
                        if not event:
                            mb.showerror("Error", "Event not found.")
                            return
                        event_name, event_date = event

                        cursor.execute("""
                            SELECT Price FROM EventTicketType 
                            WHERE EventID = %s AND TicketType = %s
                        """, (self.event_id, ticket_type))
                        price = cursor.fetchone()
                        if not price:
                            mb.showerror("Error", "Ticket price information not found.")
                            return
                        ticket_price = price[0]

                except Exception as e:
                    mb.showerror("Error", f"Unable to print ticket: {e}")
                    return

        sanitized_customer_phone = re.sub(r'[\\/:*?"<>| ]', '', customer_phone)
        if not sanitized_customer_phone:
            sanitized_customer_phone = "Unknown"
        sanitized_event_name = re.sub(r'[\\/:*?"<>|]', '_', event_name).replace(' ', '_')
        filename = f"{sanitized_customer_phone}_{sanitized_event_name}_ticket.txt"

        # Get the current time in UTC+07:00 (Asia/Bangkok timezone)
        try:
            tz = pytz.timezone("Asia/Bangkok")
            current_time = datetime.now(tz)
            formatted_time = current_time.strftime("%I:%M %p +07 on %A, %B %d, %Y")
        except Exception as e:
            mb.showerror("Error", f"Unable to fetch current time: {e}")
            formatted_time = "Unknown Time"

        # Write ticket details to file
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("===== Sports Ticketing System - Ticket Receipt =====\n")
                f.write(f"Issued on: {formatted_time}\n")
                f.write("-" * 50 + "\n")
                f.write("Customer Information:\n")
                f.write(f"Name: {customer_name}\n")
                f.write(f"Phone Number: {customer_phone}\n")
                f.write("-" * 50 + "\n")
                f.write("Ticket Information:\n")
                f.write(f"Event: {event_name}\n")
                f.write(f"Date: {event_date}\n")
                f.write(f"Ticket Type: {ticket_type}\n")
                f.write(f"Seat Number: {seat_number}\n")
                f.write(f"Price: ${ticket_price}\n")
                f.write("-" * 50 + "\n")
                f.write("Thank you for your purchase!\n")

            mb.showinfo("Success", f"Ticket receipt exported successfully to {filename}")

        except Exception as e:
            mb.showerror("Error", f"Unable to write ticket to file: {e}")

    def remove_selected_ticket(self):
        selected = self.customer_tree.selection()
        if not selected:
            mb.showerror("Selection Error", "Please select a ticket from the Treeview to remove.")
            return
        try:
            values = self.customer_tree.item(selected[0])["values"]
            customer_id = values[0]
            event_name = values[4]
            ticket_type = values[5]
            seat_number = values[6]

            if not customer_id or not event_name or not ticket_type or not seat_number:
                mb.showerror("Error", "Selected ticket has incomplete data.")
                return

            with db_cursor() as cursor:
                cursor.execute("START TRANSACTION")

                # Find the TicketID and EventID for the selected ticket
                cursor.execute("""
                    SELECT t.TicketID, t.EventID
                    FROM Tickets t
                    JOIN Events e ON t.EventID = e.EventID
                    WHERE t.CustomerID = %s AND e.EventName = %s AND t.TicketType = %s
                    AND (
                        SELECT s2.SeatNumber
                        FROM Seats s2
                        WHERE s2.EventID = t.EventID
                        AND s2.SeatType = t.TicketType
                        AND s2.Status = 'Booked'
                        AND (
                            SELECT COUNT(*)
                            FROM Tickets t2
                            WHERE t2.EventID = t.EventID
                            AND t2.TicketType = t.TicketType
                            AND t2.TicketID <= t.TicketID
                        ) = (
                            SELECT COUNT(*)
                            FROM Seats s3
                            WHERE s3.EventID = s2.EventID
                            AND s3.SeatType = s2.SeatType
                            AND s3.Status = 'Booked'
                            AND s3.SeatNumber <= s2.SeatNumber
                        )
                    ) = %s
                """, (customer_id, event_name, ticket_type, seat_number))
                ticket = cursor.fetchone()
                if not ticket:
                    cursor.execute("ROLLBACK")
                    mb.showerror("Error", "Ticket not found in the database.")
                    return
                ticket_id, event_id = ticket

                # Find the SeatID for the selected seat, ensuring it matches the EventID
                cursor.execute("""
                    SELECT SeatID
                    FROM Seats
                    WHERE SeatNumber = %s AND SeatType = %s AND Status = 'Booked' AND EventID = %s
                """, (seat_number, ticket_type, event_id))
                seat = cursor.fetchone()
                if not seat:
                    cursor.execute("ROLLBACK")
                    mb.showerror("Error", "Seat not found or already available.")
                    return
                seat_id = seat[0]

                # Delete the ticket
                cursor.execute("DELETE FROM Tickets WHERE TicketID = %s", (ticket_id,))

                # Update the seat status to Available
                cursor.execute("UPDATE Seats SET Status = 'Available' WHERE SeatID = %s", (seat_id,))

                cursor.execute("COMMIT")

            mb.showinfo("Success", f"Ticket for seat {seat_number} removed successfully!")
            self.refresh_customer_tree()
            # Clear the selection after removal
            self.customer_tree.selection_remove(selected)

        except Exception as e:
            mb.showerror("Error", f"Unable to remove ticket: {e}")

class TicketingApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sports Ticketing System")
        self.geometry("1200x800")

        self.frames = {
            "Role": RoleSelector(self, self),
            "Admin": AdminPage(self),
            "Manager": ManagerPage(self),
            "Cashier": CashierPage(self)
        }

        self.show_role_page("Role")

    def show_role_page(self, role):
        for f in self.frames.values():
            f.pack_forget()
        self.frames[role].pack()

if __name__ == "__main__":
    app = TicketingApp()
    app.mainloop()
