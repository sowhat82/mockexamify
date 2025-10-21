"""
Admin Support Tickets Management for MockExamify
Complete ticket viewing and response system
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

import config
from auth_utils import AuthUtils, run_async


def show_ticket_detail_modal():
    """Display detailed view of a single ticket"""
    ticket = st.session_state.viewing_ticket

    st.markdown("## 🎫 Ticket Details")
    st.markdown("---")

    # Ticket header
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"### #{ticket.get('id')} - {ticket.get('subject')}")
        st.markdown(f"**From:** {ticket.get('user_email')}")
        st.markdown(f"**Category:** {ticket.get('category')}")
        st.markdown(f"**Created:** {ticket.get('created_at')}")

    with col2:
        status = ticket.get("status", "Open")
        priority = ticket.get("priority", "Medium")

        # Status badge
        status_colors = {
            "Open": "🔴",
            "In Progress": "🟡",
            "Pending": "🔵",
            "Resolved": "🟢",
            "Closed": "⚪",
        }
        st.markdown(f"**Status:** {status_colors.get(status, '❓')} {status}")
        st.markdown(f"**Priority:** {priority}")

    st.markdown("---")

    # Description
    st.markdown("### 📄 Description")
    st.info(ticket.get("description", "No description provided"))

    # Additional technical details
    st.markdown("### 🔧 Technical Details")
    col1, col2 = st.columns(2)

    with col1:
        if ticket.get("browser"):
            st.markdown(f"**Browser:** {ticket.get('browser')}")
        if ticket.get("device"):
            st.markdown(f"**Device:** {ticket.get('device')}")

    with col2:
        if ticket.get("error_message"):
            st.markdown(f"**Error Message:** `{ticket.get('error_message')}`")

    # Responses (if any)
    if ticket.get("responses"):
        st.markdown("---")
        st.markdown("### 💬 Responses")
        for idx, response in enumerate(ticket.get("responses", [])):
            with st.expander(f"Response {idx + 1} - {response.get('created_at', '')}"):
                st.markdown(f"**From:** {response.get('responder', 'Unknown')}")
                st.markdown(response.get("message", ""))

    st.markdown("---")

    # Action buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💬 Respond to Ticket", use_container_width=True, type="primary"):
            st.session_state.responding_to_ticket = ticket
            del st.session_state.viewing_ticket
            st.rerun()

    with col2:
        if ticket.get("status") not in ["Resolved", "Closed"]:
            if st.button("✅ Mark as Resolved", use_container_width=True):
                success = run_async(update_ticket_status(ticket.get("id"), "Resolved"))
                if success:
                    st.success("Ticket marked as resolved!")
                    del st.session_state.viewing_ticket
                    st.rerun()

    with col3:
        if st.button("🔙 Back to List", use_container_width=True):
            del st.session_state.viewing_ticket
            st.rerun()


def show_ticket_response_modal():
    """Display form to respond to a ticket"""
    ticket = st.session_state.responding_to_ticket

    st.markdown("## 💬 Respond to Ticket")
    st.markdown("---")
    st.markdown(f"**Ticket:** #{ticket.get('id')} - {ticket.get('subject')}")
    st.markdown(f"**User:** {ticket.get('user_email')}")
    st.markdown("---")

    with st.form("ticket_response_form"):
        response_message = st.text_area(
            "Response Message", height=200, placeholder="Type your response here..."
        )

        new_status = st.selectbox(
            "Update Status",
            ["Keep Current", "In Progress", "Pending", "Resolved"],
            help="Change ticket status with your response",
        )

        col1, col2 = st.columns(2)

        with col1:
            send_response = st.form_submit_button(
                "📤 Send Response", type="primary", use_container_width=True
            )

        with col2:
            cancel_response = st.form_submit_button("❌ Cancel", use_container_width=True)

        if send_response:
            if response_message:
                # Send response
                success = run_async(send_ticket_response(ticket.get("id"), response_message))

                if success:
                    # Update status if changed
                    if new_status != "Keep Current":
                        run_async(update_ticket_status(ticket.get("id"), new_status))

                    st.success("✅ Response sent successfully!")
                    del st.session_state.responding_to_ticket
                    st.rerun()
                else:
                    st.error("❌ Failed to send response")
            else:
                st.error("⚠️ Please enter a response message")

        if cancel_response:
            del st.session_state.responding_to_ticket
            st.rerun()


async def send_ticket_response(ticket_id: str, message: str) -> bool:
    """Send response to ticket"""
    try:
        from db import db

        # Add response to ticket
        success = await db.add_ticket_response(ticket_id, message, "admin")
        return success
    except Exception as e:
        st.error(f"Error sending response: {str(e)}")
        return False


async def update_ticket_status(ticket_id: str, new_status: str) -> bool:
    """Update ticket status"""
    try:
        from db import db

        return await db.update_support_ticket_status(ticket_id, new_status)
    except Exception as e:
        st.error(f"Error updating ticket: {str(e)}")
        return False


def show_admin_tickets():
    """Display admin support tickets management page"""
    auth = AuthUtils(config.API_BASE_URL)

    # Check admin authentication
    if not auth.is_authenticated() or not auth.is_admin():
        st.error("⛔ Unauthorized Access - Admin Only")
        st.stop()

    # Check if we're viewing a ticket details modal
    if "viewing_ticket" in st.session_state:
        show_ticket_detail_modal()
        return

    # Check if we're responding to a ticket
    if "responding_to_ticket" in st.session_state:
        show_ticket_response_modal()
        return

    # Back button
    if st.button("⬅️ Back to Dashboard", key="back_to_dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()

    # Header
    st.markdown("## 🎫 Support Tickets Management")
    st.markdown("*Manage and respond to user support requests*")

    # Tabs for different ticket views
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📥 All Tickets", "🔥 Open Tickets", "✅ Resolved", "📊 Statistics"]
    )

    with tab1:
        show_all_tickets()

    with tab2:
        show_open_tickets()

    with tab3:
        show_resolved_tickets()

    with tab4:
        show_ticket_statistics()


def show_all_tickets():
    """Display all support tickets"""
    # Custom CSS to make labels black and header
    st.markdown(
        """
        <style>
        .stSelectbox > label, .stTextInput > label {
            color: #000000 !important;
        }
        </style>
        <h3 style="color: #000000;">📥 All Support Tickets</h3>
    """,
        unsafe_allow_html=True,
    )

    # Filters
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status_filter = st.selectbox(
            "Status",
            ["All", "Open", "In Progress", "Pending", "Resolved", "Closed"],
            key="status_filter_all",
        )

    with col2:
        priority_filter = st.selectbox(
            "Priority", ["All", "Low", "Medium", "High", "Urgent"], key="priority_filter_all"
        )

    with col3:
        category_filter = st.selectbox(
            "Category",
            [
                "All",
                "Technical Issue",
                "Payment & Billing",
                "Account & Login",
                "Exam Content",
                "Feature Request",
                "Bug Report",
                "Other",
            ],
            key="category_filter_all",
        )

    with col4:
        sort_by = st.selectbox(
            "Sort By", ["Newest First", "Oldest First", "Priority", "Status"], key="sort_by_all"
        )

    # Search
    search_query = st.text_input(
        "🔍 Search tickets",
        placeholder="Search by ticket ID, subject, or user email...",
        key="search_all",
    )

    # Load tickets
    with st.spinner("Loading tickets..."):
        tickets = run_async(
            load_all_tickets(status_filter, priority_filter, category_filter, sort_by, search_query)
        )

    # Display ticket count
    st.markdown(
        f'<p style="color: #000000;"><strong>Found {len(tickets)} ticket(s)</strong></p>',
        unsafe_allow_html=True,
    )

    if not tickets:
        st.info("📭 No tickets found matching your filters.")
        return

    # Display tickets
    for ticket in tickets:
        display_ticket_card(ticket, key_prefix="all_")


def show_open_tickets():
    """Display only open tickets"""
    st.markdown('<h3 style="color: #000000;">🔥 Open Tickets</h3>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color: #000000; font-style: italic;">Tickets requiring immediate attention</p>',
        unsafe_allow_html=True,
    )

    # Load open tickets
    with st.spinner("Loading open tickets..."):
        tickets = run_async(load_tickets_by_status("Open"))

    if not tickets:
        st.success("🎉 No open tickets! All caught up.")
        return

    # Display tickets
    for ticket in tickets:
        display_ticket_card(ticket, show_quick_actions=True, key_prefix="open_")


def show_resolved_tickets():
    """Display resolved tickets"""
    st.markdown('<h3 style="color: #000000;">✅ Resolved Tickets</h3>', unsafe_allow_html=True)

    # Load resolved tickets
    with st.spinner("Loading resolved tickets..."):
        tickets = run_async(load_tickets_by_status("Resolved"))

    if not tickets:
        st.info("📭 No resolved tickets yet.")
        return

    st.markdown(f"**{len(tickets)} resolved ticket(s)**")

    # Display tickets
    for ticket in tickets:
        display_ticket_card(ticket, compact=True, key_prefix="resolved_")


def show_ticket_statistics():
    """Display ticket statistics and analytics"""
    st.markdown('<h3 style="color: #000000;">📊 Ticket Statistics</h3>', unsafe_allow_html=True)

    # Load statistics
    with st.spinner("Loading statistics..."):
        stats = run_async(get_ticket_statistics())

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Tickets", stats.get("total", 0), delta=f"+{stats.get('new_today', 0)} today"
        )

    with col2:
        st.metric(
            "Open Tickets",
            stats.get("open", 0),
            delta=stats.get("open_change", 0),
            delta_color="inverse",
        )

    with col3:
        st.metric(
            "Avg Response Time",
            stats.get("avg_response_time", "0h"),
            delta=stats.get("response_time_trend", "0h"),
        )

    with col4:
        resolution_rate = stats.get("resolution_rate", 0)
        st.metric(
            "Resolution Rate", f"{resolution_rate}%", delta=f"{stats.get('resolution_trend', 0)}%"
        )

    st.markdown("---")

    # Status breakdown
    st.markdown(
        '<h4 style="color: #000000;">📋 Ticket Status Breakdown</h4>', unsafe_allow_html=True
    )
    col1, col2 = st.columns(2)

    with col1:
        status_data = stats.get("by_status", {})
        for status, count in status_data.items():
            st.markdown(
                f'<p style="color: #000000;"><strong>{status}:</strong> {count}</p>',
                unsafe_allow_html=True,
            )

    with col2:
        priority_data = stats.get("by_priority", {})
        st.markdown(
            '<p style="color: #000000;"><strong>Priority Distribution:</strong></p>',
            unsafe_allow_html=True,
        )
        for priority, count in priority_data.items():
            emoji = {"Low": "🟢", "Medium": "🟡", "High": "🟠", "Urgent": "🔴"}.get(priority, "⚪")
            st.markdown(
                f'<p style="color: #000000;">{emoji} <strong>{priority}:</strong> {count}</p>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Category breakdown
    st.markdown('<h4 style="color: #000000;">📂 Tickets by Category</h4>', unsafe_allow_html=True)
    category_data = stats.get("by_category", {})

    for category, count in sorted(category_data.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / stats.get("total", 1)) * 100
        st.progress(percentage / 100, text=f"{category}: {count} ({percentage:.1f}%)")


def display_ticket_card(
    ticket: Dict[str, Any],
    show_quick_actions: bool = False,
    compact: bool = False,
    key_prefix: str = "",
):
    """Display a ticket card"""
    ticket_id = ticket.get("id", "Unknown")
    subject = ticket.get("subject", "No subject")
    user_email = ticket.get("user_email", "Unknown user")
    status = ticket.get("status", "Open")
    priority = ticket.get("priority", "Medium")
    category = ticket.get("category", "General")
    created_at = ticket.get("created_at", "")
    description = ticket.get("description", "")

    # Status colors
    status_colors = {
        "Open": "#e74c3c",
        "In Progress": "#f39c12",
        "Pending": "#3498db",
        "Resolved": "#27ae60",
        "Closed": "#95a5a6",
    }

    # Priority emojis
    priority_emojis = {"Low": "🟢", "Medium": "🟡", "High": "🟠", "Urgent": "🔴"}

    status_color = status_colors.get(status, "#95a5a6")
    priority_emoji = priority_emojis.get(priority, "🟡")

    # Format date
    try:
        date_obj = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        formatted_date = date_obj.strftime("%b %d, %Y %I:%M %p")
        time_ago = get_time_ago(date_obj)
    except:
        formatted_date = "Unknown date"
        time_ago = ""

    # Ticket card
    with st.container():
        st.markdown(
            f"""
        <div style="
            border: 1px solid #e1e5e9;
            border-left: 4px solid {status_color};
            border-radius: 0.5rem;
            padding: {'1rem' if compact else '1.5rem'};
            margin-bottom: 1rem;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        ">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                <div style="flex: 1;">
                    <h4 style="margin: 0; color: #2c3e50;">#{ticket_id} - {subject}</h4>
                    <p style="margin: 0.3rem 0 0 0; color: #7f8c8d; font-size: 0.9rem;">
                        👤 {user_email} • 📂 {category}
                    </p>
                    {f'<p style="margin: 0.3rem 0 0 0; color: #7f8c8d; font-size: 0.85rem;">⏱️ {time_ago}</p>' if time_ago else ''}
                </div>
                <div style="text-align: right;">
                    <div style="background: {status_color}; color: white; padding: 0.3rem 0.8rem; border-radius: 1rem; font-size: 0.75rem; font-weight: bold; margin-bottom: 0.5rem;">
                        {status}
                    </div>
                    <div style="font-size: 0.85rem; color: #7f8c8d;">
                        {priority_emoji} {priority}
                    </div>
                </div>
            </div>
        """,
            unsafe_allow_html=True,
        )

        # Description preview (if not compact)
        if not compact and description:
            preview = description[:150] + "..." if len(description) > 150 else description
            st.markdown(
                f"""
            <div style="color: #4a5568; font-size: 0.9rem; margin: 0.75rem 0; padding: 0.75rem; background: #f8f9fa; border-radius: 0.5rem;">
                {preview}
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # Action buttons
        if show_quick_actions:
            col1, col2, col3, col4 = st.columns(4)
        else:
            col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("👁️ View", key=f"{key_prefix}view_{ticket_id}", use_container_width=True):
                view_ticket_details(ticket)

        with col2:
            if status not in ["Resolved", "Closed"]:
                if st.button(
                    "💬 Respond", key=f"{key_prefix}respond_{ticket_id}", use_container_width=True
                ):
                    show_response_form(ticket)

        with col3:
            if status == "Open" and show_quick_actions:
                if st.button(
                    "🚀 Take", key=f"{key_prefix}take_{ticket_id}", use_container_width=True
                ):
                    update_ticket_status(ticket_id, "In Progress")

        with col4:
            if status not in ["Resolved", "Closed"]:
                if st.button(
                    "✅ Resolve", key=f"{key_prefix}resolve_{ticket_id}", use_container_width=True
                ):
                    resolve_ticket(ticket_id)


def view_ticket_details(ticket: Dict[str, Any]):
    """Display full ticket details in a modal"""
    st.session_state.viewing_ticket = ticket
    st.rerun()


def show_response_form(ticket: Dict[str, Any]):
    """Show response form for a ticket"""
    st.session_state.responding_to_ticket = ticket
    st.rerun()


def resolve_ticket(ticket_id: str):
    """Mark ticket as resolved"""
    success = run_async(update_ticket_status(ticket_id, "Resolved"))
    if success:
        st.success("✅ Ticket marked as resolved")
        st.rerun()
    else:
        st.error("❌ Failed to update ticket status")


def get_time_ago(date_obj: datetime) -> str:
    """Get human-readable time ago"""
    now = datetime.now(date_obj.tzinfo) if date_obj.tzinfo else datetime.now()
    diff = now - date_obj

    if diff.days > 365:
        return f"{diff.days // 365} year(s) ago"
    elif diff.days > 30:
        return f"{diff.days // 30} month(s) ago"
    elif diff.days > 0:
        return f"{diff.days} day(s) ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600} hour(s) ago"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60} minute(s) ago"
    else:
        return "Just now"


# Database functions
async def load_all_tickets(
    status: str, priority: str, category: str, sort_by: str, search: str
) -> List[Dict[str, Any]]:
    """Load all tickets with filters"""
    try:
        from db import db

        tickets = await db.get_all_support_tickets()

        # Apply filters
        if status != "All":
            tickets = [t for t in tickets if t.get("status") == status]

        if priority != "All":
            tickets = [t for t in tickets if t.get("priority") == priority]

        if category != "All":
            tickets = [t for t in tickets if t.get("category") == category]

        if search:
            search_lower = search.lower()
            tickets = [
                t
                for t in tickets
                if search_lower in str(t.get("id", "")).lower()
                or search_lower in t.get("subject", "").lower()
                or search_lower in t.get("user_email", "").lower()
            ]

        # Apply sorting
        if sort_by == "Newest First":
            tickets.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        elif sort_by == "Oldest First":
            tickets.sort(key=lambda x: x.get("created_at", ""))
        elif sort_by == "Priority":
            priority_order = {"Urgent": 0, "High": 1, "Medium": 2, "Low": 3}
            tickets.sort(key=lambda x: priority_order.get(x.get("priority", "Medium"), 2))
        elif sort_by == "Status":
            tickets.sort(key=lambda x: x.get("status", ""))

        return tickets
    except Exception as e:
        st.error(f"Error loading tickets: {str(e)}")
        return []


async def load_tickets_by_status(status: str) -> List[Dict[str, Any]]:
    """Load tickets by status"""
    try:
        from db import db

        tickets = await db.get_all_support_tickets()
        return [t for t in tickets if t.get("status") == status]
    except Exception as e:
        st.error(f"Error loading tickets: {str(e)}")
        return []


async def get_ticket_statistics() -> Dict[str, Any]:
    """Get ticket statistics"""
    try:
        from db import db

        tickets = await db.get_all_support_tickets()

        total = len(tickets)

        # Count by status
        by_status = {}
        for ticket in tickets:
            status = ticket.get("status", "Open")
            by_status[status] = by_status.get(status, 0) + 1

        # Count by priority
        by_priority = {}
        for ticket in tickets:
            priority = ticket.get("priority", "Medium")
            by_priority[priority] = by_priority.get(priority, 0) + 1

        # Count by category
        by_category = {}
        for ticket in tickets:
            category = ticket.get("category", "Other")
            by_category[category] = by_category.get(category, 0) + 1

        # Calculate metrics
        open_count = by_status.get("Open", 0)
        resolved_count = by_status.get("Resolved", 0)
        resolution_rate = (resolved_count / total * 100) if total > 0 else 0

        # Count today's tickets
        today = datetime.now().date()
        new_today = sum(
            1
            for t in tickets
            if datetime.fromisoformat(t.get("created_at", "").replace("Z", "+00:00")).date()
            == today
        )

        return {
            "total": total,
            "open": open_count,
            "new_today": new_today,
            "resolution_rate": round(resolution_rate, 1),
            "avg_response_time": "< 24h",  # Calculate based on response times
            "by_status": by_status,
            "by_priority": by_priority,
            "by_category": by_category,
            "open_change": 0,  # Calculate trend
            "response_time_trend": "0h",
            "resolution_trend": 0,
        }
    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")
        return {}


async def update_ticket_status(ticket_id: str, new_status: str) -> bool:
    """Update ticket status"""
    try:
        from db import db

        return await db.update_support_ticket_status(ticket_id, new_status)
    except Exception as e:
        st.error(f"Error updating ticket: {str(e)}")
        return False
