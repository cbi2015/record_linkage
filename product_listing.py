import argparse
import logging
import logging.config
import traceback
import inspect
import os
from collections import defaultdict
import simplejson
import glob
import random
import string


def get_args():
    parser = argparse.ArgumentParser(description="Invite customers based on distance from headquarters")
    parser.add_argument('-p',
                        '--products_file',
                        type=str,
                        help="Provide file_name with the path eg: ../../test_data/client_list.txt",
                        required=True)
    parser.add_argument('-l',
                        '--listings_file',
                        type=str,
                        help="Default distance is 100 km",
                        required=True)
    parser.add_argument('-c',
                        '--log_config',
                        type=str,
                        help="log config of python logging in json",
                        required=False,
                        default=None)
    args = parser.parse_args()
    return args


def setup_log(args):
    default_script_path = os.path.abspath(os.path.dirname(__file__))
    log_config = default_script_path + "/logconfig.json"
    if args.log_config:
        log_config = args.log_config
    try:
        # creating default log location, if it does not exists
        if not os.path.isdir(default_script_path+'/logs/'):
            os.makedirs(default_script_path+'/logs/')
        config_data = simplejson.load(open(log_config, 'r'))
        logging.config.dictConfig(config_data)
        # log_message('log setup successfully based on the config {0}'.format(log_config), logging.INFO)
    except:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
        frame = inspect.currentframe()
        log_message('loading of log config failed', logging.ERROR, frame)


def log_message(message, log_level, frame=None, log_name=None):
    # if log_name is not given, default internal logger will be used
    logger = logging.getLogger(log_name)
    # Errors are logged with the stack details, to give more context
    # Debug is put in else instead of elif, to basically put any logs other than
    # INFO and ERROR to debug
    if log_level == logging.ERROR:
        logger.error((message.decode('utf-8')))
        func = inspect.currentframe().f_code
        logger.error("%s in %s:%i" % (func.co_name, func.co_filename, func.co_firstlineno))
        stack_trace = traceback.format_stack(frame)
        logger.exception("Unhandled error occured")
        logger.exception(''.join(stack_trace))
    elif log_level == logging.INFO:
        logger.info((message.decode('utf-8')))
    else:
        logger.debug((message.decode('utf-8')))


class Product(object):

    def __init__(self, product_dict):
        self.product_name = product_dict['product_name']
        self.manufacturer = product_dict['manufacturer']
        self.model = product_dict['model']
        # optional data so we use .get function as None is stored, if data is not present
        self.family = product_dict.get('family')
        # 2010-01-06T19:00:00.000-05:00
        self.announced_date = product_dict['announced-date']

    def get_product_name(self):
        return self.product_name


class Listing(object):

    def __init__(self, listing_dict):
        self.title = listing_dict['title']
        self.manufacturer = listing_dict['manufacturer']
        self.currency = listing_dict['currency']
        self.price = str(listing_dict['price'])


def process_input_files(inut_file_name, input_type):
    result = defaultdict(lambda: [])
    if input_type == 'product':
        result = {}
    with open(inut_file_name, 'rb') as input_file:
        counter = 0
        for line in input_file:
            counter += 1
            try:
                result_data = simplejson.loads(line.strip())
                log_message("json loaded succesfully", logging.INFO)
                if input_type == 'product':
                    result[result_data["manufacturer"]] = Product(result_data)
                else:
                    result[result_data["manufacturer"]].append(Listing(result_data))
                log_message(
                                "{0}: line {1} processed sucessfully".format(inut_file_name, str(counter)),
                                logging.INFO
                            )
            except:
                frame = inspect.currentframe()
                log_message(
                                "{0}: processing of line {1} failed".format(inut_file_name, str(counter)),
                                logging.ERROR, frame
                            )
    return result


def map_products_list(product_map, listing_map):
    product_listings = defaultdict(lambda: [])
    for data in listing_map:
        if data in product_map:
            # extend is faster than append if we want to attach list of elements to a existing list
            product_listings[product_map[data].get_product_name()].extend(listing_map[data])
    return product_listings


def writeToFile(result_map):
    # Added random file name generator, to avoid clobbering the results file by multiple runs
    result_qualifier = len(glob.glob('results_file_*'))
    randomstr_value = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    result_file_name = 'results_file_' + str(result_qualifier) + '_' + randomstr_value
    # printing the name of the file for user information and for programs parsing stdout
    print result_file_name
    log_message("Results are stored in {0}".format(result_file_name), logging.INFO)
    with open(result_file_name, 'wb') as result_file:
        for data in result_map:
            try:
                listings = [d for d in result_map[data]]
                result_text = simplejson.dumps(
                                                {
                                                    "product_name": data,
                                                    "listings": listings
                                                },
                                                default=lambda o: o.__dict__,
                                                ensure_ascii=False
                                              )
                result_file.write(result_text.encode('utf-8') + '\n')
            except:
                frame = inspect.currentframe()
                log_message("Error writing the result, check if inut data is correct",
                            logging.ERROR, frame)


def main():
    args = get_args()
    try:
        # The logging module is setup below, just once and we use it then in all places
        setup_log(args)
        # processing the products file
        products = process_input_files(args.products_file, "product")
        # processing the listings file
        listings = process_input_files(args.listings_file, "listings")
        # creating a map from products to list, using manufacturer as key
        product_to_list = map_products_list(products, listings)
        # writing the results to the file
        writeToFile(product_to_list)
    except:
        frame = inspect.currentframe()
        log_message('Exception in Main', logging.ERROR, frame)


if __name__ == '__main__':
    main()
