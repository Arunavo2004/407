
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import time  # For simulating real-time updates

# Function to generate synthetic dummy data
@st.cache_data  # Cache to avoid regenerating on every rerun
def generate_data():
    # Dates: From Nov 1 to Nov 15, 2025, but extend to current date for demo (Nov 23, 2025)
    start_date = datetime(2025, 11, 1)
    end_date = datetime(2025, 11, 23, 23, 59)  # Extend to current date for realism
    dates = pd.date_range(start_date, end_date, freq='T')  # Every minute
    
    # Rooms: 3 floors, 3 rooms each
    rooms = ['101', '102', '103', '201', '202', '203', '301', '302', '303']
    floors = ['1']*3 + ['2']*3 + ['3']*3
    
    data = []
    for room, floor in zip(rooms, floors):
        for date in dates:
            voltage = np.random.uniform(220, 240)  # Random realistic voltage
            current = np.random.uniform(5, 10) if date.hour >= 8 and date.hour < 20 else 0  # Off at night, current 0
            power = voltage * current  # Power in watts
            energy_kwh = power / 1000 / 60  # Energy per minute in kWh
            bill_taka = energy_kwh * 5  # Assume 5 taka per kWh
            carbon_gco2 = energy_kwh * 500  # Assume 500g CO2 per kWh
            # Status: Scheduled off between 8 PM - 8 AM
            status = 'off' if date.hour < 8 or date.hour >= 20 else 'on'
            data.append([date, room, floor, voltage, current, power, energy_kwh, bill_taka, carbon_gco2, status])
    
    df = pd.DataFrame(data, columns=['timestamp', 'room_id', 'floor', 'voltage', 'current', 'power', 
                                     'energy_kwh', 'bill_taka', 'carbon_gco2', 'status'])
    return df

# Load data
data_df = generate_data()

# Simulate device management: Store devices in session state (one device per room initially)
if 'devices' not in st.session_state:
    st.session_state.devices = {room: f'device_{room}' for room in data_df['room_id'].unique()}

# App title
st.title("Building Energy Management System (BEMS) for FUB Building")

# Sidebar for navigation and global controls
st.sidebar.title("Navigation")
view_mode = st.sidebar.selectbox("Select View", ["Building Overview", "Floor Summary", "Room Details", "Device Management"])

# Custom date range for all views
st.sidebar.subheader("Custom Date Range")
start_date = st.sidebar.date_input("Start Date", datetime(2025, 11, 1))
end_date = st.sidebar.date_input("End Date", datetime(2025, 11, 23))
filtered_df = data_df[(data_df['timestamp'].dt.date >= start_date) & (data_df['timestamp'].dt.date <= end_date)]

# Simulate real-time update: Refresh button
if st.sidebar.button("Refresh Dashboard"):
    st.rerun()

# View 1: Building Overview - Central dashboard with tiles for rooms
if view_mode == "Building Overview":
    st.header("Building Overview")
    # Calculate building totals
    total_energy = filtered_df['energy_kwh'].sum()
    total_bill = filtered_df['bill_taka'].sum()
    total_carbon = filtered_df['carbon_gco2'].sum()
    st.metric("Total Energy (kWh)", f"{total_energy:.2f}")
    st.metric("Total Bill (Taka)", f"{total_bill:.2f}")
    st.metric("Total Carbon (gCO2)", f"{total_carbon:.2f}")
    
    # Tiles for each room
    st.subheader("Room Tiles")
    room_summaries = filtered_df.groupby('room_id').agg({
        'power': 'mean',
        'status': 'last',
        'energy_kwh': 'sum',
        'bill_taka': 'sum',
        'carbon_gco2': 'sum'
    }).reset_index()
    
    cols = st.columns(3)  # 3 columns for tiles
    for idx, row in room_summaries.iterrows():
        with cols[idx % 3]:
            st.markdown(f"**Room {row['room_id']}**")
            st.write(f"Avg Power: {row['power']:.2f} W")
            st.write(f"Status: {row['status']}")
            st.write(f"Energy: {row['energy_kwh']:.2f} kWh")
            if st.button(f"View Details for {row['room_id']}", key=f"btn_{row['room_id']}"):
                st.session_state.selected_room = row['room_id']
                st.session_state.view_mode = "Room Details"  # Simulate navigation

# View 2: Floor Summary
elif view_mode == "Floor Summary":
    st.header("Floor Summary")
    selected_floor = st.selectbox("Select Floor", sorted(filtered_df['floor'].unique()))
    floor_df = filtered_df[filtered_df['floor'] == selected_floor]
    
    # Floor totals
    floor_energy = floor_df['energy_kwh'].sum()
    floor_bill = floor_df['bill_taka'].sum()
    floor_carbon = floor_df['carbon_gco2'].sum()
    st.metric("Floor Energy (kWh)", f"{floor_energy:.2f}")
    st.metric("Floor Bill (Taka)", f"{floor_bill:.2f}")
    st.metric("Floor Carbon (gCO2)", f"{floor_carbon:.2f}")
    
    # Graph for floor power trend
    floor_trend = floor_df.groupby('timestamp')['power'].sum().reset_index()
    st.plotly_chart(px.line(floor_trend, x='timestamp', y='power', title=f"Floor {selected_floor} Power Trend"))

# View 3: Room Details
elif view_mode == "Room Details":
    st.header("Room Details")
    selected_room = st.selectbox("Select Room", sorted(filtered_df['room_id'].unique()), index=0)
    room_df = filtered_df[filtered_df['room_id'] == selected_room]
    
    if not room_df.empty:
        # Latest values (simulate real-time)
        latest = room_df.iloc[-1]
        col1, col2, col3 = st.columns(3)
        col1.metric("Voltage", f"{latest['voltage']:.2f} V")
        col2.metric("Current", f"{latest['current']:.2f} A")
        col3.metric("Power", f"{latest['power']:.2f} W")
        
        col4, col5, col6 = st.columns(3)
        total_energy = room_df['energy_kwh'].sum()
        total_bill = room_df['bill_taka'].sum()
        total_carbon = room_df['carbon_gco2'].sum()
        col4.metric("Energy (kWh)", f"{total_energy:.2f}")
        col5.metric("Bill (Taka)", f"{total_bill:.2f}")
        col6.metric("Carbon (gCO2)", f"{total_carbon:.2f}")
        
        # Graphs
        st.subheader("Graphs")
        st.plotly_chart(px.line(room_df, x='timestamp', y='voltage', title="Voltage Graph"))
        st.plotly_chart(px.line(room_df, x='timestamp', y='current', title="Current Graph"))
        st.plotly_chart(px.line(room_df, x='timestamp', y='power', title="Power Graph"))
        
        # Manual Controls
        st.subheader("Manual Controls")
        if st.button("Turn On AC"):
            st.success("AC Turned On (Simulated)")
            # In real, update status
        if st.button("Turn Off AC"):
            st.success("AC Turned Off (Simulated)")
        
        # Scheduled On/Off
        st.subheader("Scheduled On/Off")
        on_time = st.time_input("Schedule On Time", value=datetime.strptime("08:00", "%H:%M").time())
        off_time = st.time_input("Schedule Off Time", value=datetime.strptime("20:00", "%H:%M").time())
        if st.button("Apply Schedule"):
            st.info(f"Schedule applied: On at {on_time}, Off at {off_time}. Estimated 20% savings in electricity cost.")
        
        # Status
        st.write(f"Current Status: {latest['status']}")

# View 4: Device Management
elif view_mode == "Device Management":
    st.header("Device Management")
    st.write("Manage devices (one per room for simplicity, but extensible)")
    
    # Display current devices
    devices_df = pd.DataFrame(list(st.session_state.devices.items()), columns=['Room', 'Device ID'])
    st.dataframe(devices_df)
    
    # Add device
    new_room = st.text_input("New Room ID")
    new_device = st.text_input("New Device ID")
    if st.button("Add/Update Device"):
        if new_room and new_device:
            st.session_state.devices[new_room] = new_device
            st.success(f"Added/Updated device {new_device} for room {new_room}")
    
    # Delete device
    delete_room = st.selectbox("Select Room to Delete", list(st.session_state.devices.keys()))
    if st.button("Delete Device"):
        del st.session_state.devices[delete_room]
        st.success(f"Deleted device for room {delete_room}")

# Footer
st.markdown("---")
st.caption("Demo project for CSE407 - Green Computing. Data is synthetic and simulated.")
