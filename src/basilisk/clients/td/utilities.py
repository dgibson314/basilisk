import configparser

def get_app_info():
    config = configparser.ConfigParser()
    config.read("basilisk.conf")
    return (config['credentials']['CLIENT_ID'], config['credentials']['REDIRECT_URI'])
