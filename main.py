# this is needed for conversions that need IERS data
#import pyodide_http
#pyodide_http.patch_all()
import inspect

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

def get_selected_cosmo_cls():
    selelem = Element('cosmology-class')
    class_name = selelem.element.value
    return getattr(cosmology, class_name)


def get_selected_method(bound=False):
    method_name = Element('cosmo-methods').element.value
    if bound:
        return getattr(get_cosmology_object(), method_name)
    else:
        return getattr(get_selected_cosmo_cls(), method_name)

def populate_cosmology_class_dropdown():
    selelem = Element('cosmology-class')

    class_names = get_all_subclasses(cosmology.Cosmology)
    for nm in ('Cosmology', 'FLRW'):
        if nm in class_names:
            class_names.remove(nm)
    class_names.sort()

    selelem.element.innerHTML = '\n'.join([f'<option value="{nm}">{nm}</option>' for nm in class_names])

    cosmo_class_change()


def populate_parameters_table():
    global cosmo_table_header  # ugggh
    table_elements = [cosmo_table_header]

    cosmo_cls = get_selected_cosmo_cls()

    param_names = cosmo_cls.__parameters__
    init_sig = inspect.signature(cosmo_cls.__init__)
    defaults = [''
                if init_sig.parameters[pnm].default is init_sig.parameters[pnm].empty else
                init_sig.parameters[pnm].default 
                for pnm in param_names]
    
    for pnm, default in zip(param_names, defaults):
        table_elements.append(f'<tr><td>{pnm}</td><td><input type="text" id="{pnm}-value" value="{default}"></td></tr>')

    Element('cosmo-parameter-table').element.innerHTML = '\n'.join(table_elements)

def get_cosmology_object():
    cosmo_cls = get_selected_cosmo_cls()
    param_names = cosmo_cls.__parameters__

    input_elems = [Element(f'{pnm}-value') for pnm in param_names]
    input_kwargs = {pnm:None if elem.element.value == 'None' else u.Quantity(elem.element.value) 
                    for pnm, elem in zip(param_names, input_elems)}

    return cosmo_cls(**input_kwargs)


def populate_methods_dropdown(meths):
    selelem = Element('cosmo-methods')
    selelem.element.innerHTML = '\n'.join([f'<option value="{meth}">{meth}</option>' for meth in meths])

def cosmo_class_change():
    meths = get_redshift_methods(get_selected_cosmo_cls(), include_private=False, include_z2=True)
    populate_methods_dropdown(meths)
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