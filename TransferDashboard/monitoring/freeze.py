from flask.ext.frozen import Freezer
from application import app
import sys

app.config['FREEZER_BASE_URL'] = sys.argv[1]
app.config['FREEZER_DESTINATION'] = sys.argv[2]
freezer = Freezer(app)

if __name__ == '__main__':
    freezer.freeze()
