"""
    Utilities for the admin app
"""
from django.views.generic.base import TemplateView


def auto_patterns(module, prefix='', overview=False, namespace=''):
    """
        Automatically creates URL patterns for a given module
    """
    from django.conf.urls import patterns
    if overview and not prefix:
        raise ValueError("Prefix can't be empty if overview is True")
    urls = get_urls(module, prefix, overview, namespace)
    return patterns(module.__name__, *urls)


def get_urls(module, prefix, overview, namespace):
    """Generates URLs for views decorated with `@auto_url` inside `module`"""
    from django.conf.urls import url

    def f():
        pass

    urls = []
    for name, thing in vars(module).items():
        # Only bother with things actually defined in this module
        if getattr(thing, '__module__', None) == module.__name__:
            if not getattr(thing, 'auto_url', False):
                continue

            # `thing` is a class, and we need the view function
            if type(thing) is type:
                thing = thing.as_view()

            if prefix:
                pattern = r'^%s/%s/$' % (prefix, funcname(thing))
            else:
                pattern = r'^%s/$' % funcname(thing)

            urls.append(
                url(pattern, thing, {}, name=funcname(thing))
            )

    if overview:
        pattern = r'^%s/$' % prefix
        urlname = '%s-overview' % get_module_name(module)

        # Copy URLs so that the overview doesn't include itself
        u = urls[:]
        urls.append(
            url(pattern, make_overview(module, u, namespace), name=urlname)
        )

    return urls


def make_overview(module, urls, namespace):
    """Given the URLs for a bunch of views and the module they came from this
    generates an overview page with a title, description and a list of links
    to execute the views.
    """
    title = get_module_name(module).title()
    description = module.__doc__

    class OverView(TemplateView):
        template_name = 'auto_task_overview.html'

        def get_context_data(self, **kwargs):
            ctx = super(OverView, self).get_context_data(**kwargs)
            ctx.update({'title': title, 'description': description})

            view_links = []
            for url in urls:
                view = url.callback
                view_links.append({
                    'url_name': '%s:%s' % (
                        namespace, url.name
                    ) if namespace else url.name,
                    'view_name': funcname(view, rep=' '),
                    'view_description': view.__doc__ or '',
                })

            ctx['view_links'] = sorted(
                view_links, key=lambda d: d['view_name'])
            return ctx

    return OverView.as_view()


def get_module_name(module):
    """
        Gets the module name from a module object
    """
    return module.__name__.rsplit('.')[-1]


def funcname(fn, rep='-'):
    """
        Gets the name of a function from a function object
    """
    return fn.func_name.replace('_', rep)
