import inspect
import warnings

# always an iffy life choice to suppress deprecations... but otherwise it appears on the web page
warnings.filterwarnings("ignore", category=DeprecationWarning) 

import numpy as np

import astropy
from astropy import cosmology
from astropy import units as u

# this one unnecessarily includes pytest... maybe this can be refactored?
from astropy.cosmology.tests.helper import get_redshift_methods



def get_all_subclasses(cls):
    # https://stackoverflow.com/questions/3862310/how-to-find-all-the-subclasses-of-a-class-given-its-name
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass.__qualname__)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses

def get_selected_cosmo():
    """
    Note this might be a class or might be an instance
    """
    selelem = Element('cosmology-class')
    cname = selelem.element.value.split(' (')[0]
    return getattr(cosmology, cname)


def get_selected_method(bound=False):
    method_name = Element('cosmo-methods').element.value
    if bound:
        return getattr(get_cosmology_object(), method_name)
    else:
        return getattr(get_selected_cosmo(), method_name)

def populate_cosmology_class_dropdown():
    selelem = Element('cosmology-class')

    class_names = get_all_subclasses(cosmology.Cosmology)
    for nm in ('Cosmology', 'FLRW'):
        if nm in class_names:
            class_names.remove(nm)
    class_names.sort()

    class_names += [f'{cnm} ({getattr(cosmology, cnm).__class__.__name__})' for cnm in cosmology.available]

    selelem.element.innerHTML = '\n'.join([f'<option value="{nm}">{nm}</option>' for nm in class_names])

    cosmo_class_change()


def populate_parameters_table():
    global cosmo_table_header  # ugggh
    table_elements = [cosmo_table_header]

    selected_cosmo = get_selected_cosmo()

    param_names = selected_cosmo.__parameters__
    if inspect.isclass(selected_cosmo):
        init_sig = inspect.signature(selected_cosmo.__init__)
        defaults = [''
                    if init_sig.parameters[pnm].default is init_sig.parameters[pnm].empty else
                    init_sig.parameters[pnm].default 
                    for pnm in param_names]
    else:
        defaults = [getattr(selected_cosmo, pnm) for pnm in param_names]
    
    for pnm, default in zip(param_names, defaults):
        table_elements.append(f'<tr><td>{pnm}</td><td><input type="text" id="{pnm}-value" value="{default}"></td></tr>')

    Element('cosmo-parameter-table').element.innerHTML = '\n'.join(table_elements)

def get_cosmology_object():
    cosmo_cls = get_selected_cosmo()
    if not inspect.isclass(cosmo_cls):
        cosmo_cls = cosmo_cls.__class__
    param_names = cosmo_cls.__parameters__

    input_elems = [Element(f'{pnm}-value') for pnm in param_names]

    input_kwargs = {}
    for pnm, elem in zip(param_names, input_elems):
        if elem.element.value == 'None':
            input_kwargs[pnm] = None
        elif ']' in elem.element.value:
            # this is the case where there is an array-Quantity. As of the time of this writing only relevant for m_nu
            pieces = elem.element.value.split(']')

            # TODO: work out better logic for how to do this that doesn't depend on various somewhat brittle assumptions
            assert len(pieces) == 2
            assert(pieces[0][0] == '[')

            arrstr = pieces[0][1:]
            unitstr = pieces[1]

            # DeprecationWarning: string or file could not be read to its end due to unmatched data; this will raise a ValueError in the future.
            arr = np.fromstring(arrstr, sep=' ')
            arr_comma = np.fromstring(arrstr, sep=',')
            # assume the larger is the correct one
            if len(arr_comma) > len(arr):
                arr = arr_comma

            input_kwargs[pnm] = u.Quantity(arr, unitstr) 
        else:
            input_kwargs[pnm] = u.Quantity(elem.element.value) 

    return cosmo_cls(**input_kwargs)


def populate_methods_dropdown():
    meths = sorted(get_redshift_methods(get_selected_cosmo(), include_private=False, include_z2=True))

    selelem = Element('cosmo-methods')
    prev_value = selelem.value

    selelem.element.innerHTML = '\n'.join([f'<option value="{meth}">{meth}</option>' for meth in meths])
    if prev_value in meths:
        selelem.element.value = prev_value


def cosmo_class_change():
    populate_methods_dropdown()
    cosmo_method_change()
    populate_parameters_table()

def cosmo_method_change():
    update_method_arguments()
    meth = get_selected_method()
    Element('docs-or-output').element.innerHTML = f'<h3>{meth.__name__}</h3>' + meth.__doc__.strip().replace('\n', '<br>')

def update_method_arguments():
    z_elem = Element('z-span')
    z1_elem = Element('z1-span')
    z2_elem = Element('z2-span')
    ivalue_elem = Element('invert-value-span')

    sig = inspect.signature(get_selected_method())

    z12 = None
    if 'z1' in sig.parameters and 'z2' in sig.parameters:
        z12 = True
    elif 'z' in sig.parameters:
        z12 = False
    #else,  probably something unexpected has happened - so that means disable the input below

    if Element('inverse').element.checked:
        z_elem.element.style.display = 'none'
        z1_elem.element.style.display = 'none'
        z2_elem.element.style.display = 'none'

        Element('value-to-invert').element.disabled = Element('calculate-button').disabled = z12 is not False
        ivalue_elem.element.style.display = 'inline'
    else:
        if z12:
            z_elem.element.style.display = 'none'
            z1_elem.element.style.display = 'inline'
            z2_elem.element.style.display = 'inline'
        else:
            z_elem.element.style.display = 'inline'
            z1_elem.element.style.display = 'none'
            z2_elem.element.style.display = 'none'
            Element('z-input').disabled = Element('calculate-button').disabled = z12 is None

        ivalue_elem.element.style.display = 'none'
 

def calculate():
    meth = get_selected_method(bound=True)

    z_elem = Element('z-span')
    ivalue_elem = Element('invert-value-span')

    if z_elem.element.style.display != 'none':
        # single redshift
        z = float(Element('z-input').value)
        result = meth(z)
    elif ivalue_elem.element.style.display != 'none':
        # inverse
        valstr = Element('value-to-invert').value
        if valstr == 'None':
            val = None
        else:
            val = u.Quantity(valstr)
        result = cosmology.z_at_value(meth, val)
    else: 
        # z1/z2 case
        z1 = float(Element('z1-input').value)
        z2 = float(Element('z2-input').value)
        result = meth(z1, z2)
    
    Element('docs-or-output').element.innerHTML = str(result)

def init():
    # ugggh global variables.  But this is the recommended way to save such things according to various DOM-related docs 🤷
    global cosmo_table_header
    cosmo_table_header = Element('cosmo-parameter-table').element.innerHTML

    astropy_vers_elem = Element("astropy-version")
    astropy_vers_elem.element.innerHTML = astropy.__version__

    populate_cosmology_class_dropdown()


    # lastly, hide the initializing and show the main content div
    init_div = Element("initializing-div")
    content_div = Element("main-content-div")
    init_div.element.style.display = 'none'
    content_div.element.style.display = 'block'

init()