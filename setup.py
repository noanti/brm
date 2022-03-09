from setuptools import setup

setup(
    name='brm',
    author_email='noanti001@gmail.com',
    version='0.0.1',
    packages=['brm'],
    entry_points={
        'console_scripts': ['brm=brm.__init__:main']
    },
    install_requires=[
        'httpx[http2]',
        'tqdm',
    ],
)

