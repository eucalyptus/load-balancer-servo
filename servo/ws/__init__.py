import boto
import boto.utils
from boto.ec2.elb import ELBConnection
from boto.ec2.regioninfo import RegionInfo
from boto.ec2.cloudwatch import CloudWatchConnection
from boto.iam.connection import IAMConnection
from servo.ws.loadbalancer import LoadBalancer
import servo.config as config
import servo.hostname_cache as hostname_cache
from servo.security.server_cert import ServerCertificate
import time
import M2Crypto
from collections import Iterable

def connect_euare(host_name=None, port=config.get_webservice_port(), path="services/Euare", aws_access_key_id=None, aws_secret_access_key=None, security_token=None, **kwargs):
    return EucaEuareConnection(host=config.get_euare_service_url(), port=port, path=path, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, security_token=security_token, **kwargs)

class StatefulInstance(object):
    def __init__(self, instance_id=None, state=None):
        self.instance_id = instance_id
        self.state = state

    def __repr__(self):
        return '%s:%s' % (self.instance_id, self.state)

    def __str__(self):
        return self.__repr__()

    def startElement(self, name, attrs, connection):
        return None
 
    def endElement(self, name, value, connection):
        if name == 'InstanceId':
            self.instance_id = value
        elif name == 'InstanceState':
            self.instance_state = value
        else:
            setattr(self, name, value)

class EucaEuareConnection(IAMConnection):
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=False, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, host=None, debug=0, 
                 https_connection_factory=None, path='/', security_token=None, validate_certs=True):
        """
        Euca-specific extension to boto's IAM connection. 
        """
        IAMConnection.__init__(self, aws_access_key_id,
                            aws_secret_access_key,
                            is_secure, port, proxy,
                            proxy_port, proxy_user, proxy_pass,
                            host, debug, https_connection_factory,
                            path, security_token,
                            validate_certs=validate_certs)

    def download_server_certificate(self, cert, pk, euare_cert, auth_signature, cert_arn):
        """
        Download server certificate identified with 'cert_arn'. del_certificate and auth_signature
        represent that the client is authorized to download the certificate

        :type cert_arn: string
        :param cert_arn: The ARN of the server ceritifcate to download
 
        :type delegation_certificate: string
        :param delegation_certificate: The certificate to show that this client is delegated to download the user's server certificate

        :type auth_signature: string
        :param auth_signature: The signature by Euare as a proof that the bearer of delegation_certificate is authorized to download server certificate
 
        """
        timestamp = boto.utils.get_ts()
        msg= cert_arn+"&"+timestamp
        rsa = M2Crypto.RSA.load_key_string(pk)
        msg_digest = M2Crypto.EVP.MessageDigest('sha256')
        msg_digest.update(msg)
        sig = rsa.sign(msg_digest.digest(),'sha256')
        sig = sig.encode('base64')
        cert = cert.encode('base64')

        params = {'CertificateArn': cert_arn,
                  'DelegationCertificate': cert,
                  'AuthSignature':auth_signature,
                  'Timestamp':timestamp,
                  'Signature':sig} 
        resp = self.get_response('DownloadServerCertificate', params)
        result = resp['euca:_download_server_certificate_response_type']['euca:download_server_certificate_result']
        if not result:
            return None
        sig = result['euca:signature']
        arn = result['euca:certificate_arn']
        server_cert = result['euca:server_certificate']
        server_pk = result['euca:server_pk'] 
   
        if arn != cert_arn:
            raise Exception("certificate ARN in the response is not valid")

        sig_payload=str(server_cert)+'&'+str(server_pk)
        sig = str(sig)
        # verify the signature to ensure the response came from EUARE
        cert = M2Crypto.X509.load_cert_string(euare_cert)
        verify_rsa = cert.get_pubkey().get_rsa()
        msg_digest = M2Crypto.EVP.MessageDigest('sha256')
        msg_digest.update(sig_payload)
        if verify_rsa.verify(msg_digest.digest(), sig.decode('base64'), 'sha256') != 1 :
            raise Exception("invalid signature from EUARE")

        # prep symmetric keys
        parts = server_pk.split("\n")
        if(len(parts) != 2):
            raise Exception("invalid format of server private key")
        symm_key = parts[0]
        cipher = parts[1] 
        try:
            raw_symm_key = rsa.private_decrypt(symm_key.decode('base64'), M2Crypto.RSA.pkcs1_padding)
        except Exception, err:
            raise Exception("failed to decrypt symmetric key: " + str(err))
        try:
            cipher = cipher.decode('base64')
            # prep iv and cipher text
            iv = cipher[0:16]
            cipher_text = cipher[16:]

            # decrypt the pk
            cipher = M2Crypto.EVP.Cipher("aes_256_cbc", raw_symm_key , iv, op = 0, padding=0)
            txt = cipher.update(cipher_text)
            txt = txt + cipher.final()
            s_cert = ServerCertificate(server_cert.decode('base64'), txt.decode('base64'))
        except Exception, err:
            raise Exception("failed to decrypt the private key: " + str(err)) 

        return s_cert
 
