from datetime import  datetime # date
import io
import csv
# import json
# from time import process_time_ns
# from traceback import print_tb
# from typing import final  
from dateutil import parser
import os
import sys
# Add the root project directory to sys.path at the beginning
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from operator import or_ , and_#, truediv
# from pickle import NONE
from cof.mail_management import send_mail

from flask.globals import  request#current_app,
from flask.helpers import  send_file#flash,, url_for
from cof.models.model import CompanyCustomer, ForumPost, Member, PersonalityCategory, PersonalityTestResult, \
     company_test_results_highchart  , Company , company_join_approval,Employee, CompanyPosition, MemberRole #Personality, PersonalityCompatibility
# from cof.models.model import *
from flask import jsonify
from flask import Blueprint#, render_template, abort, redirect
from cof.models import db
from .auth import login_required
from cof.decorators import corporate_admin_required
from flask_login import login_required, current_user

from sqlalchemy import text,cast, String
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import aliased


print("hello check silent reposetery ")
corporate_api = Blueprint('corporate_api', __name__, url_prefix='/api/corporate/admin')

# @corporate_api.route('/users', methods=['GET'])
# def get_users():
#     if not current_user.is_authenticated:
#         return jsonify({"error": "Unauthorized access"}), 401  

#     print(f"DEBUG: Logged-in User ID: {current_user.id}")  # ✅ Yeh ID print karega terminal me

#     company_user = db.session.query(CompanyCustomer).filter(CompanyCustomer.id == current_user.id).first()

#     if not company_user:
#         print("DEBUG: User not found in CompanyCustomer table")  # ✅ Yeh print hoga agar user nahi mila
#         return jsonify({"error": "User not associated with any company."}), 404

#     return jsonify({
#         "message": "User exists in CompanyCustomer table",
#         "user_id": current_user.id,
#         "company_id": company_user.company_id
#     })





@corporate_api.route('/users', methods=['GET'])
def get_users():
    if not current_user.is_authenticated:
        return jsonify({"error": "Unauthorized access"}), 401  

    print(f"DEBUG: Logged-in User ID: {current_user.id}")  # ✅ Debugging
    
    company_user = db.session.query(CompanyCustomer).filter(CompanyCustomer.id == current_user.id).first()
    if not company_user:
        print("DEBUG: User not found in CompanyCustomer table")  # ✅ Debugging
        return jsonify({"error": "User not associated with any company."}), 404

    # Fetch users in the same company
    users_query = db.session.query(CompanyCustomer).filter(
        CompanyCustomer.company_id == company_user.company_id
    )

    search = request.args.get('search', '').strip()
    if search:
        search_term = f"%{search}%"
        users_query = users_query.join(Member).filter(
            or_(
                Member.name.ilike(search_term),
                Member.avatar_name.ilike(search_term)
            )
        )

    users = users_query.all()
    company = db.session.query(Company).filter(Company.id == company_user.company_id).first()
    if not company:
        return jsonify({"error": "Company not found."}), 404

    team_admin = db.session.query(Member).filter(Member.id == current_user.id).first()
    receive_mails = team_admin.can_send_email if team_admin else False

    # Prepare response
    users_list = [
        {
            "id": user.id,
            "name": user.member.name,
            "avatar_image": user.member.avatar_image,
            "position": "Member" if user.position.name == "employee" else user.position.name
        }
        for user in users
    ]

    return jsonify({
        "users": users_list,
        "company_name": company.name,
        "receive_mails": receive_mails,
        "current_user_id": current_user.id
    }), 200

    
@corporate_api.route('/pendingUsers', methods=['GET'])
def get_pending_users():
    """
    API to list all pending user join requests for the logged-in corporate admin's company.

    Response:
    - JSON object with pending user details.
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "Unauthorized access"}), 401

    # Get the logged-in user's company information
    company_user = db.session.query(CompanyCustomer).filter(CompanyCustomer.id == current_user.id).first()
    if not company_user:
        return jsonify({"error": "User not associated with any company."}), 404
    
    company_id = company_user.company_id  # Get the company_id from the user

    # Raw SQL query to get pending users from company_join_approval table
    query = text("""
        SELECT cja.member_id, m.name AS member_name, cja.applied_on
        FROM company_join_approval cja
        JOIN member m ON cja.member_id = m.id
        WHERE cja.company_id = :company_id AND cja.approval_status = 0
    """)

    # Execute the query and fetch the results
    result = db.session.execute(query, {"company_id": company_id}).fetchall()

    # Prepare the list of pending users
    users_list = []
    for row in result:
        users_list.append({
            "member_id": row.member_id,
            "name": row.member_name,
            "applied_on": row.applied_on.strftime("%d-%b-%y") if row.applied_on else None
        })

    # Get the company name
    company = db.session.query(Company).filter(Company.id == company_id).first()
    if not company:
        return jsonify({"error": "Company not found."}), 404

    # Return the response
    return jsonify({
        "pending_users": users_list,
        "company_name": company.name
    }), 200





# @corporate_api.route('/pendingUsers', methods=['GET'])
# def get_pending_users():
#     """
#     API to list all pending user join requests for the logged-in corporate admin's company.

#     Response:
#     - JSON object with pending user details.
#     """
#     if not current_user.is_authenticated:
#         return jsonify({"error": "Unauthorized access"}), 401

#     # Get the logged-in user's company information
#     company_user = db.session.query(CompanyCustomer).filter(CompanyCustomer.id == current_user.id).first()
#     if not company_user:
#         return jsonify({"error": "User not associated with any company."}), 404
    
#     # Fetch pending user requests for the same company
#     pending_users = db.session.query(company_join_approval).filter(
#         and_(
#             company_join_approval.company_id == company_user.company_id,
#             company_join_approval.approval_status == 0
#         )
#     ).all()

#     # Prepare the list of pending users
#     users_list = []
#     for user in pending_users:
#         member = db.session.query(Member).filter(Member.id == user.member_id).first()
#         if member:
#             users_list.append({
#                 "id": member.id,
#                 "name": member.name,
#                 "email": member.email,
#                 "applied_on": user.applied_on.strftime("%d-%b-%y")
#             })

#     # Get the company name
#     company = db.session.query(Company).filter(Company.id == company_user.company_id).first()
#     if not company:
#         return jsonify({"error": "Company not found."}), 404

#     # Return the response
#     return jsonify({
#         "pending_users": users_list,
#         "company_name": company.name
#     }), 200

    
    
@corporate_api.route('/requestAction/<int:user_id>/<int:flag>', methods=['POST'])
@login_required
@corporate_admin_required
def request_action(current_user, user_id, flag):
    """
    API to approve or reject a user request to join a company.

    Parameters:
    - user_id (int): ID of the user whose request is being processed.
    - flag (int): 1 to approve, 0 to reject.

    Response:
    - JSON object indicating success or failure.
    """
    # Fetch the logged-in admin's company
    company_user = db.session.query(CompanyCustomer).filter(CompanyCustomer.id == current_user.id).first()
    if not company_user:
        return jsonify({"error": "User not associated with any company."}), 404

    # Fetch the user's join request
    user_request = db.session.query(company_join_approval).filter(
        company_join_approval.member_id == user_id,
        company_join_approval.company_id == company_user.company_id,
        company_join_approval.approval_status == 0
    ).first()
    if not user_request:
        return jsonify({"error": "No pending request found for the specified user."}), 404

    # Process the request based on the flag
    if int(flag) == 1:  # Approve the request
        try:
            # Create Employee and CompanyCustomer entries
            new_employee = Employee(id=user_id, address="", phone="")
            db.session.add(new_employee)

            new_company_customer = CompanyCustomer(
                id=user_id,
                company_id=company_user.company_id,
                position=CompanyPosition.employee
            )
            db.session.add(new_company_customer)

            # Update the Member's role
            member = db.session.query(Member).filter_by(id=user_id).first()
            member.role = MemberRole.company,

            # Update the approval status
            user_request.approval_status = 1
            user_request.approved_on = datetime.now()
            user_request.approved_by = current_user.id

            # Fetch company details
            company = db.session.query(Company).filter(Company.id == company_user.company_id).first()

            # Send notification email
            mail_html = (
                f"Hello {member.name},<br>"
                f"Update from MakeChoice<br><br>"
                f"Congratulations! Your request to join team {company.name} has been approved.<br>"
                '<a href="https://www.makechoice.org/login">Sign in</a> to see more details.<br>'
            )
            send_mail(
                subject='Changing Our Futures - Account UPDATE',
                sender='contact.mycof.org@gmail.com',
                recipients=[member.email],
                mail_body="",
                mail_html=mail_html
            )

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to approve request: {str(e)}"}), 500

    else:  # Reject the request
        try:
            db.session.delete(user_request)
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to reject request: {str(e)}"}), 500

    # Commit the changes
    db.session.commit()

    return jsonify({"message": "Request processed successfully."}), 200




@corporate_api.route('/tests', methods=['GET'])
@login_required
@corporate_admin_required
def get_tests(current_user):
    """
    API to fetch personality test results with search, date filters, and CSV download option.

    Query Parameters:
    - search (str): Search term for email or avatar name.
    - start_date (str): Filter start date (format: YYYY-MM-DD).
    - end_date (str): Filter end date (format: YYYY-MM-DD).
    - downcsv (bool): Flag to download results as CSV.

    Response:
    - JSON object with personality test data or a downloadable CSV file.
    """
    search = '%{}%'.format(request.args.get('search', ''))
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    download = request.args.get('downcsv', False)

    # Validate date range
    if start_date and end_date and start_date > end_date:
        return jsonify({"error": "Start date must be before end date"}), 400

    # Initialize filters
    company_user = db.session.query(CompanyCustomer).filter(CompanyCustomer.id == current_user.id).first()
    if not company_user:
        return jsonify({"error": "Company user not found"}), 404

    company_customers = db.session.query(CompanyCustomer).filter(
        CompanyCustomer.company_id == company_user.company_id
    ).all()
    company_customer_ids = [customer.id for customer in company_customers]

    # Fetch tests
    if start_date and end_date:
        tests = db.session.query(PersonalityTestResult).outerjoin(CompanyCustomer).filter(
            CompanyCustomer.company_id == company_user.company_id,
            or_(CompanyCustomer.email.like(search), CompanyCustomer.avatar_name.like(search)),
            PersonalityTestResult.date_test_taken.between(start_date, end_date)
        ).order_by(PersonalityTestResult.date_test_taken.desc()).all()
    else:
        tests = db.session.query(PersonalityTestResult).all()

    # Process test data
    users_list = []
    for test in tests:
        if test.member.id in company_customer_ids:
            user_dict = {
                'test_id': test.id,
                'date': test.date_test_taken.strftime("%Y-%m-%d"),
                'email': test.member.email,
                'member_id': test.member.id,
                'avatar_name': test.member.avatar_name,
                'mood': test.mood,
                'personality_code': test.personality.code,
                'personality_name': test.personality.name,
                'personality_category': test.personality.category.name
            }
            users_list.append(user_dict)

    # Handle CSV download
    if download:
        proxy = io.StringIO()
        writer = csv.writer(proxy)
        writer.writerow([
            'Date Test Taken', 'User Email', 'User Avatar Name', 'Mood', 
            'Personality Category', 'Personality Code', 'Personality Name'
        ])
        for user in users_list:
            writer.writerow([
                user['date'], user['email'], user['avatar_name'], user['mood'], 
                user['personality_category'], user['personality_code'], user['personality_name']
            ])
        mem = io.BytesIO()
        mem.write(proxy.getvalue().encode())
        mem.seek(0)
        proxy.close()
        return send_file(
            mem, mimetype='text/csv', as_attachment=True, 
            attachment_filename='Personality_Insight.csv', cache_timeout=0
        )

    # Fetch categories for additional context
    categories = [
        {"id": category.id, "name": category.name}
        for category in db.session.query(PersonalityCategory).order_by(PersonalityCategory.id).all()
    ]

    return jsonify({
        "tests": users_list,
        "categories": categories,
        "filters": {
            "search": request.args.get('search', ''),
            "start_date": start_date,
            "end_date": end_date
        }
    })
    
    

@corporate_api.route('/compatibility/<int:user_id>', methods=['GET'])
@login_required
@corporate_admin_required
def get_compatibility(current_user, user_id):
    """
    API to fetch compatibility data for a user.

    Path Parameters:
    - user_id (int): The ID of the user to fetch compatibility data for.

    Response:
    - JSON object containing compatibility data, including users, dates, and scores.
    """
    # Fetch Personality Test Result
    ptr = db.session.query(PersonalityTestResult).filter(PersonalityTestResult.member_id == user_id).first()
    if not ptr:
        return jsonify({
            "users": [],
            "name": None,
            "dates": [],
            "scores": [],
            "testTaken": False
        })

    # Fetch related data
    company_user = db.session.query(CompanyCustomer).filter(CompanyCustomer.id == user_id).first()
    member = db.session.query(Member).filter(Member.id == user_id).first()

    # Compatibility data query
    compatibility_data = db.session.query(company_test_results_highchart).filter(
        or_(
            company_test_results_highchart.company_id == company_user.company_id,
            company_test_results_highchart.company_id == None
        )
    ).order_by(company_test_results_highchart.month_year.asc()).all()

    # Filter data for the specific user
    filtered_data = [
        entry for entry in compatibility_data
        if entry.person_1 == ptr.member.name or entry.person_1 is None
    ]

    # Extract unique dates
    unique_dates = list({entry.month_year for entry in filtered_data})

    # Gather users
    users = list({
        entry.person_2 for entry in filtered_data if entry.person_2 is not None
    })

    # Score calculation helper
    def find_score(date, user):
        for entry in filtered_data:
            if entry.month_year == date and entry.person_2 == user:
                return entry.score
        return 50  # Default score if no data is found

    # Prepare scores for the heatmap
    scores = [
        [i, j, find_score(date, user)]
        for j, user in enumerate(users)
        for i, date in enumerate(unique_dates)
    ]

    # Format dates for the response
    formatted_dates = [
        parser.parse(date).strftime("%b-%y") for date in unique_dates
    ]

    return jsonify({
        "users": users,
        "name": ptr.member.name,
        "dates": formatted_dates,
        "scores": scores,
        "testTaken": True
    })
    



# @corporate_api.route('/posts', methods=['GET'])
# # @login_required
# # @corporate_admin_required
# def get_posts(current_user):
#     """
#     API to fetch posts for the current company.

#     Query Parameters:
#     - search (str): A search term to filter posts by user email or avatar name.

#     Response:
#     - JSON object containing a list of posts.
#     """
#     # Fetch search query
#     search = '%{}%'.format(request.args.get('search') if request.args.get('search') else '')

#     # Query posts
#     posts = db.session.query(ForumPost).outerjoin(CompanyCustomer).filter(
#         CompanyCustomer.company_id == current_user.company_id,
#         or_(
#             CompanyCustomer.email.like(search),
#             CompanyCustomer.avatar_name.like(search)
#         )
#     ).order_by(ForumPost.date_posted.desc()).all()

#     # Prepare posts data
#     posts_data = [
#         {
#             "id": post.id,
#             "title": post.title,
#             "content": post.content,
#             "author_email": post.author.email,
#             "author_name": post.author.avatar_name,
#             "date_posted": post.date_posted.strftime("%Y-%m-%d %H:%M:%S")
#         }
#         for post in posts
#     ]

#     return jsonify({
#         "posts": posts_data
#     })
# @corporate_api.route('/posts', methods=['GET'])
# def get_posts():
#     """
#     API to fetch posts for the current company.

#     Query Parameters:
#     - search (str): A search term to filter posts by position or other available fields.
#     - user_id (int): User ID to fetch the posts and user details for the given user.

#     Response:
#     - JSON object containing a list of posts and user details.
#     """
#     # Get user_id from the query parameters
#     user_id = request.args.get('user_id')

#     if not user_id:
#         return jsonify({"error": "User ID not provided"}), 400  # Return error if user_id not provided

#     try:
#         # Fetch the user details from the company_customer table based on user_id
#         company_user = db.session.query(CompanyCustomer).filter(
#             CompanyCustomer.id == user_id
#         ).first()

#         if not company_user:
#             return jsonify({"error": "User not found"}), 404  # If user is not found

#         # Check if the position is an instance of CompanyPosition and extract the name (or similar field)
#         position_value = company_user.position.name if hasattr(company_user.position, 'name') else company_user.position

#         # Fetch additional user details from the company_customer table
#         user_details = {
#             "id": company_user.id,
#             "company_id": company_user.company_id,
#             "position": position_value  # Use extracted position value
#         }

#         # Fetch search query (if provided)
#         search = '%{}%'.format(request.args.get('search') if request.args.get('search') else '')

#         # Explicit JOIN between ForumPost and Member
#         posts = db.session.query(ForumPost).select_from(ForumPost).join(
#             Member, Member.id == ForumPost.member_id  # Join ForumPost with Member via member_id
#         ).join(
#             CompanyCustomer, CompanyCustomer.id == Member.id  # Now join Member to CompanyCustomer
#         ).filter(
#             CompanyCustomer.company_id == company_user.company_id,  # Use the user's company_id
#             or_(
#                 cast(CompanyCustomer.position, String).like(search),  # Cast position to string before using LIKE
#                 Member.name.like(search)  # Assuming you want to search by Member's name as well
#             )
#         ).order_by(ForumPost.date_posted.desc()).all()

#         # Prepare posts data
#         posts_data = [
#             {
#                 "id": post.id,
#                 "title": post.title,
#                 "content": post.content,
#                 "author_name": post.author.name,  # Assuming 'name' exists in the Member table
#                 "date_posted": post.date_posted.strftime("%Y-%m-%d %H:%M:%S")
#             }
#             for post in posts
#         ]

#         # Combine user details and posts data
#         response_data = {
#             "user_details": user_details,
#             "posts": posts_data
#         }

#         return jsonify(response_data)

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500



@corporate_api.route('/posts', methods=['GET'])
def get_posts():
    """
    API to fetch posts for the current company.
    """
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({"error": "User ID not provided"}), 400

    try:
        # Fetch the user's company ID
        company_user = db.session.query(CompanyCustomer).filter(
            CompanyCustomer.id == user_id
        ).first()

        if not company_user:
            return jsonify({"error": "User not found"}), 404

        # ✅ Convert `position` to string for JSON serialization
        position_value = str(company_user.position)  # 🔥 FIXED

        user_details = {
            "id": company_user.id,
            "company_id": company_user.company_id,
            "position": position_value
        }

        # Fetch search query
        search = '%{}%'.format(request.args.get('search', ''))

        # ✅ **Corrected SQLAlchemy Query**
        query = db.session.query(
            ForumPost.id,
            ForumPost.content,
            Member.name.label("author_name"),
            ForumPost.date_posted,
            CompanyCustomer.position,
            CompanyCustomer.company_id
        ).join(
            Member, Member.id == ForumPost.member_id
        ).join(
            CompanyCustomer, CompanyCustomer.id == Member.id  # ✅ Correct Foreign Key Relation
        ).filter(
            CompanyCustomer.company_id == company_user.company_id,
            or_(
                cast(CompanyCustomer.position, String).like(search),
                Member.name.like(search)
            )
        ).order_by(ForumPost.date_posted.desc())

        print("Generated SQL Query:", str(query))  # ✅ Debugging ke liye SQL Query print karega

        posts = query.all()

        # ✅ Convert `CompanyCustomer.position` to string before returning JSON
        posts_data = [
            {
                "id": post.id,
                "content": post.content,
                "author_name": post.author_name,
                "date_posted": post.date_posted.strftime("%Y-%m-%d %H:%M:%S"),
                "position": str(post.position),  # 🔥 FIXED
                "company_id": post.company_id
            }
            for post in posts
        ]

        response_data = {
            "user_details": user_details,
            "posts": posts_data
        }

        return jsonify(response_data)

    except Exception as e:
        print("Error:", str(e))  # ✅ Debugging ke liye error print karega
        return jsonify({"error": str(e)}), 500












   


@corporate_api.route('/receiveMails/<int:user_id>/<int:flag>', methods=['GET'])
@login_required
@corporate_admin_required
def receiveMails(current_user, user_id , flag): 
    
    if(current_user.id != int(user_id)) : return  jsonify({"code" : 403 , "status":"Forbidden" }) 
    
    mem = db.session.query(Member).filter(Member.id == user_id).first()
    mem.can_send_email = flag
    db.session.commit()

    return  jsonify({"code" : 200 ,   "status":"Done"})