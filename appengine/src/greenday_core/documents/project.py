"""
    Search API document for Project
"""
# import lib deps
from search import indexes, fields
from search.indexers import startswith
from django.utils import timezone


# project document
class ProjectDocument(indexes.DocumentModel):
    """
        Appengine Search API document for Project
        model.
    """
    id = fields.AtomField()
    name = fields.TextField()
    owner_id = fields.AtomField()
    owner_name = fields.TextField()
    description = fields.TextField()
    assigned_users = fields.TextField()
    created = fields.DateField()
    modified = fields.DateField()
    n_grams = fields.TextField()

    @classmethod
    def from_instance(cls, project):
        """
            Factory method for creating a project document from
            a Project model instance.
        """
        doc = cls(doc_id=str(project.pk))
        copy_attrs = ['name', 'description']
        for attr in copy_attrs:
            setattr(doc, attr, getattr(project, attr, None))
        doc.id = unicode(project.pk)

        # make datetimes timezone naive as appengine doesnt support
        # indexing aware datetime objects which is annoying
        doc.created = timezone.make_naive(project.created, timezone.utc)
        doc.modified = timezone.make_naive(project.modified, timezone.utc)

        # manually add data that we cant directly copy from the instance
        if project.owner:
            doc.owner_id = unicode(project.owner.id)
            doc.owner_name = '%s %s' % (
                project.owner.first_name, project.owner.last_name)

        # add assigned users
        doc.assigned_users = ' '.join(
            str(user_id) for user_id in project.projectusers.filter(
                is_pending=False, is_assigned=True).values_list(
                    'user_id', flat=True)).strip()

        # build ngrams
        doc.n_grams = cls.make_ngrams(project.name)

        # return completed doc.
        return doc

    @classmethod
    def make_ngrams(cls, string):
        """
            Class method to generate ngrams based on the passed string
        """
        return " ".join(ngram for ngram in startswith(string[:100]))
