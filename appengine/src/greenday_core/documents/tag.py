"""
    Search API document for Tag
"""
# import lib deps
from search import indexes, fields
from search.indexers import startswith


# tag document
class AutoCompleteTagDocument(indexes.DocumentModel):
    """
        Appengine Search API document for autocompleting tags
    """
    id = fields.AtomField()
    name = fields.TextField()
    description = fields.TextField()
    image_url = fields.TextField()
    n_grams = fields.TextField()
    project_ids = fields.TextField()
    private_to_project_id = fields.AtomField()

    @classmethod
    def from_instance(cls, tag):
        """
            Factory method for creating a tag document from
            a GlobalTag model instance.
        """
        doc = cls(doc_id=str(tag.pk))
        copy_attrs = [
            'name', 'description', 'image_url']
        for attr in copy_attrs:
            setattr(doc, attr, getattr(tag, attr, None))
        doc.id = unicode(tag.pk)
        doc.n_grams = " ".join(startswith(tag.name))

        # if tag is private, set the privacy attribute and project ids
        if tag.created_from_project.tags_is_private:
            doc.private_to_project_id = unicode(tag.created_from_project_id)
            doc.project_ids = "%s" % tag.created_from_project_id
        else:
            doc.project_ids = " ".join(
                map(str, tag.projecttags.values_list("project_id", flat=True)))
        return doc
