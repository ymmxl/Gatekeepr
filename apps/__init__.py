import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module


db = SQLAlchemy()
login_manager = LoginManager()


def register_extensions(app):
    # call sqlachemy instance
    db.init_app(app)
    # initiate login manager
    login_manager.init_app(app)


def register_blueprints(app):
    # register blueprints
    for module_name in ('authentication', 'home'):
        module = import_module('apps.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)

def configure_database(app):
    #run on first time
    with app.app_context():
        db.create_all()
        
        # Create test user if it doesn't exist
        from apps.authentication.models import Users, SavedOTP
        from apps.authentication.util import hash_pass
        from apps.home.twofa import otp_gen
        
        test_user = Users.query.filter_by(username='test').first()
        if not test_user:
            test_user = Users()
            test_user.username = 'test'
            test_user.email = 'test@gatekeepr.com'
            test_user.password = hash_pass('test888')
            db.session.add(test_user)
            db.session.commit()
        
        # Reset demo OTP secrets for the test user
        # Sample OTP secrets in different formats
        DEMO_OTPS = [
            {
                "secret": "OZTY75LSB3CNSBID",  # Standard Google Authenticator format
                "friendly_name": "Google Demo Account"
            },
            {
                "secret": "otpauth://totp/Example:user@google.com?secret=NGEXUK3MMVXDQ3DF&issuer=Example",  # otpauth URL format
                "friendly_name": "Demo URL Format"
            },
            {
                "secret": "demo123|secret456|IJKU4WBTTMQGCX3FGIQVS5KXKNZHK2LT|demo@example.com",  # Full format with UID|PASSWORD|SECRET|EMAIL
                "friendly_name": "Demo Full Format"
            },
            {
                "secret": "KQ4G-C3EE-Y55U-DRNK",  # Authy format with hyphens
                "friendly_name": "Demo Authy Format"
            }
        ]
        
        # Always reset demo OTPs for the test user
        if test_user:
            # First, delete any existing OTPs for the test user
            SavedOTP.query.filter_by(user_id=test_user.id).delete()
            db.session.commit()
            
            # Then add the demo OTPs
            for demo_otp in DEMO_OTPS:
                try:
                    # Clean the secret using the otp_gen class
                    gen = otp_gen(demo_otp["secret"])
                    cleaned_secret = gen.secret
                    
                    # Create the SavedOTP record
                    saved_otp = SavedOTP(
                        user_id=test_user.id,
                        secret=cleaned_secret,
                        friendly_name=demo_otp["friendly_name"]
                    )
                    
                    db.session.add(saved_otp)
                except Exception as e:
                    print(f"Error adding OTP {demo_otp['friendly_name']}: {str(e)}")
            
            # Commit the changes
            db.session.commit()

    # end session after logout
    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove() 


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    return app
