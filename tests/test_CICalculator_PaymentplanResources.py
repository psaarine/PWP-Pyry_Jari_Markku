import pytest
import tempfile
import os
import random
import json

from CICalculator import create_app, db
from CICalculator.models import  Handle, Paymentplan, Model
from sqlalchemy.exc import IntegrityError

@pytest.fixture
def client():
    print("")
    print("Aloitus")
    
    db_fd, db_fname = tempfile.mkstemp()
    config = {
    "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
    "TESTING": True
    }
    
    app = create_app(config)
    
    app.app_context().push()
    db.create_all()
    
    _populate_db()
    
    yield app.test_client()
    
    db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)
    print("Lopetus")
    
def _get_model():
    return {"model": "compact", "manufacturer": "BMW", "year": 2000}
    
def _get_plan():
    return {"provider": "Jorma", "months": 3, "payers": 1, "price": 1200.0}

    
def _populate_db():
    item = Handle(
    handle="dummyhandle",
    name="dummyname",
    type="dummytype"
    )
    db.session.add(item)
    db.session.commit()
    
    handle = Handle.query.first()
    
    for x in range(15):
        item = Paymentplan(
        price = 1000.0,
        provider = "dummyprovider-{}".format(x),
        interestrate = 0.0,
        months = 1,
        payers = 1
        )
        if x == 3 or x == 9 or x == 12:
            item.open = False
        db.session.add(item)
        handle.paymentplans.append(item)        
        
    db.session.commit()
    
    item = Model(
    manufacturer = "Toyota",
    model = "Corolla",
    year = 2007
    )
    handle.models.append(item)
    db.session.add(item)
    db.session.commit()
    
    item = Model(
    manufacturer = "Volkswagen",
    model = "Jetta",
    year = 2009
    )
    handle.models.append(item)
    db.session.add(item)
    db.session.commit()
    
    for x in range(1, 6):
        model = Model.query.first()
        plan = Paymentplan.query.get(x)
        model.paymentplans.append(plan)
        db.session.commit()
             
    for x in range(6, 11):
        model = Model.query.get(2)
        plan = Paymentplan.query.get(x)
        model.paymentplans.append(plan)
        db.session.commit()

class TestPaymentplanCollection(object):
    
    RESOURCE_URL = "/api/dummyhandle/plans"
    
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body) == 15
        
    def test_post(self, client):
        valid = _get_plan()
        resp = client.post(self.RESOURCE_URL, json=valid)   # Tests that posting works
        assert resp.status_code == 201
        
        resp = client.get(self.RESOURCE_URL)
        body = json.loads(resp.data)
        assert len(body) == 16                              # Tests that new item is added
        
        plan = Paymentplan.query.get(16)                    # Tests that new item has submitted values
        assert plan.provider == "Jorma"
        
        valid = _get_plan()                                 # Tests that optional values work
        valid["interestrate"] = 1.2
        valid["provider"] = "Peetu"                         # Chanhed name to avoid integrity issues
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201  
        plan = Paymentplan.query.get(17)
        assert plan.interestrate == 1.2
        
        invalid = _get_plan()
        invalid.pop("provider")
        resp = client.post(self.RESOURCE_URL, json=invalid) # Tests that missing fields cause bad request
        assert resp.status_code == 400
        
        valid = _get_plan()
        resp = client.post(self.RESOURCE_URL, json=valid)   # Tests that duplicate paymentplans cause 409 error
        assert resp.status_code == 409
        
    def test_delete(self, client):
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        
    def test_put(self, client):
        valid = {"type": "petteri", "name": "jorma"}
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 200
        
        handle = Handle.query.first()
        assert handle.type == "petteri"
        
class TestOpenPaymentplanCollection(object):
    
    RESOURCE_URL = "/api/dummyhandle/plans/open"
    
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        
        body = json.loads(resp.data)
        assert len(body) == 12                              # Three of the generated paymentplans have open set to false so correct len is 12
        
class TestPaymentplanItem(object):
    
    RESOURCE_URL = "/api/dummyhandle/plans/dummyprovider-0/1000.0/1"
    WRONG_RESOURCE_URL = "/api/dummyhandle/plans/dummyprovider-0/1000.0/2"
    
    def test_get(self, client):
        # Tests that get works
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        
        # Tests 404 error
        resp = client.get(self.WRONG_RESOURCE_URL)
        assert resp.status_code == 404
        
    def test_put(self, client):
        # Tests that you can toggle paymentplan on and off with put
        
        resp = client.put(self.RESOURCE_URL)

        resp = client.get(self.RESOURCE_URL)
        body = json.loads(resp.data)
        assert body["open"] == False
        
        client.put(self.RESOURCE_URL)
        
        resp = client.get(self.RESOURCE_URL)
        body = json.loads(resp.data)
        assert body["open"] == True
        
        # Test 404
        resp = client.put(self.WRONG_RESOURCE_URL)
        assert resp.status_code == 404
        
    def test_delete(self, client):
        ''' Tests that status codes match and resource URL vanishes after delete '''
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 404
        
        
        
        
        
        
        
        
        
        
        
        