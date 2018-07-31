# -*- coding: utf-8 -*-

"""WSGI module for Bio2BEL WikiPathways."""

from bio2bel_wikipathways.manager import Manager

if __name__ == '__main__':
    manager = Manager()
    app = manager.get_flask_admin_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
