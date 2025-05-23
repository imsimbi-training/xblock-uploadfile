import logging

from xblock.core import XBlock
from xblock.fields import Scope, List
from xblock.fragment import Fragment
from xblock.runtime import Runtime

log = logging.getLogger(__name__)

class RootBlock(XBlock):
    """A simple container block for SDK."""

    def student_view(self, context=None):
        fragment = Fragment()
        children = self.runtime.get_children(self)
        log.info("Children of RootBlock: %s", children)
        for child in self.runtime.get_children(self):
            child_fragment = child.render('student_view', context)
            fragment.add_fragment(child_fragment)
        return fragment