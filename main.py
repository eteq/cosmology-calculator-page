# this is needed for conversions that need IERS data
#import pyodide_http
#pyodide_http.patch_all()
import inspect

import astropy
from astropy import cosmology

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
    selelem = Element('cosmology-class')
    class_name = selelem.element.value
    return getattr(cosmology, class_name)


def get_selected_method():
    method_name = Element('cosmo-methods').element.value
    return getattr(get_selected_cosmo(), method_name)


def populate_cosmology_class_dropdown():
    selelem = Element('cosmology-class')

    class_names = get_all_subclasses(cosmology.Cosmology)
    for nm in ('Cosmology', 'FLRW'):
        if nm in class_names:
            class_names.remove(nm)
    class_names.sort()

    selelem.element.innerHTML = '\n'.join([f'<option value="{nm}">{nm}</option>' for nm in class_names])

    cosmo_class_change()


def populate_parameters_table(inelem, outelem):
    # From the cosmology

    select_options = cosmo_cls.__parameters__

    for e in (inelem, outelem):
        e.innerHTML = select_options


def populate_methods_dropdown(meths):
    selelem = Element('cosmo-methods')
    selelem.element.innerHTML = '\n'.join([f'<option value="{meth}">{meth}</option>' for meth in meths])

def cosmo_class_change():
    meths = get_redshift_methods(get_selected_cosmo(), include_private=False, include_z2=True)
    populate_methods_dropdown(meths)
    cosmo_method_change()

def cosmo_method_change():
    update_method_arguments()

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

        Element('value-to-invert').element.disabled = z12 is not False
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
            Element('z-input').disabled = z12 is None

        ivalue_elem.element.style.display = 'none'
 

def convert():
    incoo = coordinates.SkyCoord(hin.element.value, 
                                 frame=hinf.element.value)
    toframe = houtf.element.value
    try:
        outcoo = incoo.transform_to(toframe)
    except Exception as e:
        hout.write(f"Failed to convert due to exception: {e}")
    else:
        hout.write(str(outcoo))

def init():
    astropy_vers_elem = Element("astropy-version")
    astropy_vers_elem.element.innerHTML = astropy.__version__

    populate_cosmology_class_dropdown()


    # lastly, hide the initializing and show the main content div
    init_div = Element("initializing-div")
    content_div = Element("main-content-div")
    init_div.element.style.display = 'none'
    content_div.element.style.display = 'block'




    #populate_cosmology_class_dropdown(hinf.element, houtf.element)
    #hbutton.element.disabled = False

init()