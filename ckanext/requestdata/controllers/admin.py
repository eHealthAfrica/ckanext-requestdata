try:
    # CKAN 2.7 and later
    from ckan.common import config
except ImportError:
    # CKAN 2.6 and earlier
    from pylons import config
from ckan.plugins import toolkit
from ckan.controllers.admin import AdminController
from ckan import  model
from ckan.common import c, _
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.logic as logic

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized

c = base.c
redirect = base.redirect
request = base.request
abort = base.abort

def _get_context():
    return {
        'model': model,
        'session': model.Session,
        'user': c.user or c.author,
        'auth_user_obj': c.userobj
    }

def _get_action(action, data_dict):
    return toolkit.get_action(action)(_get_context(), data_dict)

class AdminController(AdminController):
    ctrl = 'ckanext.requestdata.controllers.admin:AdminController'

    def email(self):
        '''
            Handles creating the emailt templatet in admin tab.

            :returns template
        '''
        data = request.POST
        if 'save' in data:
            try:
                data_dict = dict(request.POST)
                del data_dict['save']
                data = _get_action('config_option_update',data_dict)
            except logic.ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
                vars = {'data': data, 'errors': errors,
                        'error_summary': error_summary}
                return base.render('admin/email.html', extra_vars=vars)

            h.redirect_to(controller=self.ctrl, action='email')

        schema = logic.schema.update_configuration_schema()
        data = {}
        for key in schema:
            data[key] = config.get(key)

        vars = {'data': data, 'errors': {}}
        return toolkit.render('admin/email.html',extra_vars=vars)

    def requests_data(self):
        '''
            Handles creating template for 'Requested Data' page in the
            admin dashboard.

            :returns: template

        '''
        try:
            requests = _get_action('requestdata_requests_list', {})
            print requests
        except NotAuthorized:
            abort(403, _('Not authorized to see this page.'))

        extra_vars = {
            'requests_data' : requests
        }

        return toolkit.render('admin/all_requests_data.html', extra_vars)