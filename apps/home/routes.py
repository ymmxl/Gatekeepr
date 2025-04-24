# -*- encoding: utf-8 -*-

from apps.home import blueprint
from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
import string
import logging
from apps.home.twofa import otp_gen
from apps.authentication.models import SavedOTP
from apps import db

#initialize logger
log = logging.getLogger(__name__)

@blueprint.errorhandler(Exception)
def handle_exception(e):
    log.exception("Exception")
    return


@blueprint.route('/index')
@login_required
def index():
    return redirect('/otp.html')


@blueprint.route('/')
@login_required
def root():
    return redirect('/otp.html')


@blueprint.route('/<template>')
@login_required
def route_template(template):
    try:
        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)
        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


@blueprint.route('/otp/get-otp', methods=["POST","GET"])
@login_required
def get_form():
    if request.method == 'GET':
        if request.args:
            secret = request.args.get('secret')
            try:
                gen = otp_gen(secret)
                cleaned_secret = gen.secret  # Get the cleaned secret
                
                j = {
                    "full_secret": secret,
                    "cleaned_secret": cleaned_secret,  # Include the cleaned secret for frontend lookup
                    "secret_short": cleaned_secret[-4:] if len(cleaned_secret) >= 4 else cleaned_secret,
                    "otp": gen.get_totp(),
                    "time_left": gen.time_left()
                }   
                return jsonify(j)
            except Exception as e:
                log.exception(f"Error refreshing otp: {e}")
                return render_template('home/page-500.html',msg=f"Error generating OTP: {str(e)}"), 500
        else:
            return render_template('home/page-500.html',msg="No Args Parsed!"), 500

    else:
        form = request.get_json()
        #returns str
        if not form:
            return render_template('home/page-500.html',msg="Error submitting form"), 500
        else:
            pdata = form.strip().split("\n")
            results=[]
            errors = []
            
            for i in pdata:
                if not i.strip():  # Skip empty lines
                    continue
                
                try:
                    gen = otp_gen(i)
                    original_secret = i
                    cleaned_secret = gen.secret  # Get the cleaned secret
                    
                    j = {
                        "full_secret": original_secret,
                        "cleaned_secret": cleaned_secret, 
                        "secret_short": cleaned_secret[-4:] if len(cleaned_secret) >= 4 else cleaned_secret,
                        "otp": gen.get_totp(),
                        "time_left": gen.time_left()
                    }
                    results.append(j)
                except Exception as e:
                    log.exception(f"Error processing secret: {e}")
                    errors.append(f"Could not process secret: {i[:10]}... - {str(e)}")
            
            if not results and errors:
                error_msg = "<br>".join(errors[:5])  # Show first 5 errors
                if len(errors) > 5:
                    error_msg += f"<br>...and {len(errors) - 5} more errors"
                return render_template('home/page-500.html', msg=f"Error processing secrets:<br>{error_msg}"), 500
                
            # return html with otps rendered by jinja
            return render_template("home/otp-container.html", otps=results) if results else render_template('home/page-500.html',msg="No valid OTP secrets found"), 200


@blueprint.route('/otp/save-otp', methods=["POST"])
@login_required
def save_otp():
    try:
        data = request.get_json()
        secret = data.get('secret')
        friendly_name = data.get('friendly_name')
        
        if not secret or not friendly_name:
            return jsonify({"success": False, "message": "Secret and friendly name are required"}), 400
        
        # Clean the secret before saving
        try:
            gen = otp_gen(secret)
            cleaned_secret = gen.secret
        except Exception as e:
            log.exception(f"Error cleaning secret for saving: {e}")
            return jsonify({"success": False, "message": f"Error validating OTP secret: {str(e)}"}), 400
            
        # Check if this secret is already saved for this user
        existing = SavedOTP.query.filter_by(user_id=current_user.id, secret=cleaned_secret).first()
        if existing:
            return jsonify({"success": False, "message": "This secret is already saved"}), 400
            
        # Create new saved OTP with the cleaned secret
        saved_otp = SavedOTP(
            user_id=current_user.id,
            secret=cleaned_secret,
            friendly_name=friendly_name
        )
        
        db.session.add(saved_otp)
        db.session.commit()
        
        return jsonify({"success": True, "message": "OTP saved successfully"})
    except Exception as e:
        log.exception(f"Error saving OTP: {e}")
        return jsonify({"success": False, "message": "Error saving OTP"}), 500


@blueprint.route('/otp/get-saved-otps', methods=["GET"])
@login_required
def get_saved_otps():
    try:
        saved_otps = SavedOTP.query.filter_by(user_id=current_user.id).all()
        results = []
        
        for saved in saved_otps:
            try:
                gen = otp_gen(saved.secret)
                j = {
                    "full_secret": saved.secret,
                    "secret_short": saved.secret[-4:] if len(saved.secret) >= 4 else saved.secret,
                    "otp": gen.get_totp(),
                    "time_left": gen.time_left(),
                    "friendly_name": saved.friendly_name,
                    "saved_id": saved.id
                }
                results.append(j)
            except Exception as e:
                log.exception(f"Error generating OTP for saved secret: {e}")
                
        return render_template("home/saved-otp-container.html", otps=results) if results else ""
    except Exception as e:
        log.exception(f"Error retrieving saved OTPs: {e}")
        return "", 500


@blueprint.route('/otp/delete-saved-otp/<int:otp_id>', methods=["POST"])
@login_required
def delete_saved_otp(otp_id):
    try:
        saved_otp = SavedOTP.query.filter_by(id=otp_id, user_id=current_user.id).first()
        
        if not saved_otp:
            return jsonify({"success": False, "message": "OTP not found"}), 404
            
        db.session.delete(saved_otp)
        db.session.commit()
        
        return jsonify({"success": True, "message": "OTP deleted successfully"})
    except Exception as e:
        log.exception(f"Error deleting OTP: {e}")
        return jsonify({"success": False, "message": "Error deleting OTP"}), 500


@blueprint.route('/<template>')
@login_required
# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None



        
