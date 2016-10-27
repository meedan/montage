"""
    Search API document for User
"""
# import lib deps
from search import indexes, fields
from search.indexers import startswith

from ..models import PendingUser


# AutoCompleteUser document
class AutoCompleteUserDocument(indexes.DocumentModel):
    """
        Appengine Search API document for User / PendingUser
        model. Used to search for existing emails
        in autocompletes
    """
    user_id = fields.AtomField()
    pending_user_id = fields.AtomField()
    email = fields.TextField()
    full_name = fields.TextField()
    n_grams = fields.TextField()

    @classmethod
    def from_instance(cls, user):
        """
            Factory method for creating a AutoCompleteUser document from
            a User / PendingUser model instance.
        """
        fn_ngrams = []
        ln_ngrams = []
        doc = cls(doc_id=str(user.email))
        doc.email = user.email
        email_ngrams = cls.make_email_ngrams(user.email.lower()).split()

        if isinstance(user, PendingUser):
            doc.pending_user_id = str(user.pk)
        else:
            doc.user_id = str(user.pk)
            doc.full_name = u'%s' % user.get_full_name()
            if user.first_name:
                fn_ngrams = cls.make_ngrams(user.first_name.lower()).split()
            if user.last_name:
                ln_ngrams = cls.make_ngrams(user.last_name.lower()).split()

        # build and de-dupe the ngrams.
        ngrams = list(set(email_ngrams + fn_ngrams + ln_ngrams))
        doc.n_grams = " ".join(ngrams)
        return doc

    @classmethod
    def make_email_ngrams(cls, email):
        # build ngrams based on email address splitting on
        # @ and then any dots within the start of the address
        # this is so that we can build logical ngrams for email
        # addresses that use a firstname.lastname style prefix.
        names = email.split('@')[0].split('.')
        ngrams = [list(startswith(name)) for name in names]
        return " ".join(" ".join(map(str, ngram)) for ngram in ngrams)

    @classmethod
    def make_ngrams(cls, string):
        """
            Class method to generate ngrams based on the passed string
        """
        return " ".join(ngram for ngram in startswith(string[:100]))
