#------------------------------------------------------------------------------
# Copyright (c) 2013, Nucleic Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#------------------------------------------------------------------------------
from atom.api import Atom, Typed, ForwardTyped

from enaml.application import Application
from enaml.core.declarative import Declarative
from enaml.core.object import flag_generator, flag_property


class ProxyToolkitObject(Atom):
    """ The base class of all proxy toolkit objects.

    A ProxyToolkitObject is repsonsible for the communication between
    the Declarative declaration of the object and then implementation
    object which actually performs the behavior.

    """
    #: A reference to the ToolkitObject declaration.
    declaration = ForwardTyped(lambda: ToolkitObject)

    def destroy(self):
        """ Destroy the proxy and any of its resources.

        This method is called by the declaration when it is destroyed.
        It should be reimplemented by subclasses when more control
        is required.

        """
        del self.declaration

    def parent(self):
        """ Get the parent proxy object for this object.

        Returns
        -------
        result : QtToolkitObject or None
            The parent toolkit object of this object, or None if no
            such parent exists.

        """
        d = self.declaration.parent
        if isinstance(d, ToolkitObject):
            return d.proxy

    def children(self):
        """ Get the child objects for this object.

        Returns
        -------
        result : iterable
            An iterable of the child toolkit objects for this object.

        """
        for d in self.declaration.children:
            if isinstance(d, ToolkitObject):
                yield d.proxy


#: A flag indicating that the object's proxy is ready for use.
ACTIVE_PROXY_FLAG = flag_generator.next()


class ToolkitObject(Declarative):
    """ The base class of all toolkit objects in Enaml.

    """
    #: A reference to the ProxyToolkitObject
    proxy = Typed(ProxyToolkitObject)

    #: A property which gets and sets the active proxy flag. This should
    #: not be manipulated directly by user code. This flag will be set to
    #: True by external code after the proxy widget hierarchy is setup.
    proxy_is_active = flag_property(ACTIVE_PROXY_FLAG)

    def __init__(self, parent=None, **kwargs):
        """ Initialize a ToolkitObject.

        """
        super(ToolkitObject, self).__init__(parent, **kwargs)
        app = Application.instance()
        if app is not None:
            self.proxy = app.create_proxy(self)
        else:
            msg = 'the Application must be created before creating any '
            msg += 'instances of ToolkitObject'
            raise RuntimeError(msg)

    def destroy(self):
        """ A reimplemented destructor.

        This destructor invokes the 'destroy' method on the proxy
        toolkit object.

        """
        super(ToolkitObject, self).destroy()
        self.proxy_is_active = False
        self.proxy.destroy()
        del self.proxy

    def _update_proxy(self, change):
        """ Update the proxy widget when the Widget data changes.

        This method only updates the proxy when an attribute is updated;
        not when it is created or deleted. It is useful for subclasses
        as a base observer handler

        """
        if self.proxy_is_active and change['type'] == 'updated':
            handler = getattr(self.proxy, 'set_' + change['name'], None)
            if handler is not None:
                handler(change['newvalue'])
